"""Pinned local PDF page reader adapter; never invokes OCR, anydoc, or a network route."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import runpy
import shutil
import selectors
import signal
import subprocess
import types
import time

HERE = Path(__file__).resolve().parent
READER = HERE / 'read_extract.py'
READER_SHA256 = '19f28c155fc7e55636df628d94e254c51291d24275a78b9023786ec13b68246f'
PDFTOTEXT = '/usr/bin/pdftotext'
VIEW_HEADER = '[PDF page view: per-page plain text from the local pdftotext extractor; each [page N] section is that page\'s own text layer]'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def load_reader(path=READER, expected_sha256=READER_SHA256):
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink(), 'CANONICAL_READER_SOURCE_REQUIRED')
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected_sha256, 'PDF_READER_SOURCE_PIN_MISMATCH')
    return runpy.run_path(str(path))


def authenticate_tool(module, executable=PDFTOTEXT, expected_sha256=None, version=None):
    """Resolve the exact helper before calling the existing reader."""
    resolved = shutil.which('pdftotext')
    need(resolved == executable and Path(executable).is_absolute(), 'FIXED_PDFTOTEXT_PATH_REQUIRED')
    if expected_sha256 is not None:
        need(hashlib.sha256(Path(executable).read_bytes()).hexdigest() == expected_sha256, 'PDFTOTEXT_PIN_MISMATCH')
    if version is not None:
        need(type(version) is str and 0 < len(version) <= 128, 'PDFTOTEXT_VERSION_REQUIRED')
    return {'path': executable, 'sha256': expected_sha256, 'version': version}


class _BoundedLocalRunner:
    """Narrow subprocess API for the pinned reader; finite streams and strict UTF-8."""
    SubprocessError = subprocess.SubprocessError

    def __init__(self, data, deadline):
        self.data, self.deadline = data, deadline

    def run(self, argv, *, capture_output, timeout):
        need(type(argv) is list and len(argv) == 3 and argv[0] == 'pdftotext'
             and argv[2] == '-' and capture_output is True, 'FIXED_READER_ARGV_REQUIRED')
        path = Path(argv[1])
        need(path.is_absolute() and path.is_file() and not path.is_symlink()
             and path.stat().st_size == len(self.data) and path.read_bytes() == self.data, 'PDF_READER_BYTE_CUSTODY')
        end = min(self.deadline, time.monotonic() + min(20.0, float(timeout)))
        process, chunks = None, {'out': bytearray(), 'err': bytearray()}
        try:
            process = subprocess.Popen([PDFTOTEXT, str(path), '-'], stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                        env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
            with selectors.DefaultSelector() as selector:
                for pipe, name in ((process.stdout, 'out'), (process.stderr, 'err')):
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, name)
                while selector.get_map() or process.poll() is None:
                    need(time.monotonic() < end, 'PDF_READER_DEADLINE')
                    for key, _ in selector.select(timeout=min(.02, max(0, end-time.monotonic()))):
                        raw = os.read(key.fileobj.fileno(), 65536)
                        if not raw:
                            selector.unregister(key.fileobj)
                            continue
                        cap = 1_000_000 if key.data == 'out' else 65536
                        need(len(chunks[key.data]) + len(raw) <= cap, 'PDF_READER_STREAM_CAP')
                        chunks[key.data].extend(raw)
            process.wait(timeout=max(.01, end-time.monotonic()))
            raw = bytes(chunks['out'])
            raw.decode('utf-8', 'strict')
            need(process.returncode == 0, 'PDF_READER_NONZERO')
            return subprocess.CompletedProcess(argv, process.returncode, raw, bytes(chunks['err']))
        finally:
            if process is not None:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait(timeout=2)
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()


def read_pages(data, path, expected_sha256=READER_SHA256, deadline_monotonic=None,
               reader=None, tool=None):
    """Return page texts and the reader's authoritative page-view string.

    The injected reader/tool arguments are for offline controls only. Production
    callers leave them unset and therefore use the pinned source and local tool.
    """
    need(type(data) is bytes and 0 < len(data) <= 8_000_000 and data.startswith(b'%PDF-'), 'PDF_BYTE_OR_MAGIC_FAILURE')
    path = Path(path)
    need(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink()
         and (reader is not None or (path.stat().st_size == len(data) and path.read_bytes() == data)), 'PDF_PATH_CUSTODY_REQUIRED')
    module = load_reader(expected_sha256=expected_sha256) if reader is None else reader
    if tool is None:
        tool = authenticate_tool(module)
    remaining = None if deadline_monotonic is None else deadline_monotonic - time.monotonic()
    if remaining is not None:
        need(remaining > 0.05, 'PDF_SHARED_DEADLINE_EXHAUSTED')
    page_function = module['_pdf_page_texts']
    function_globals = getattr(page_function, '__globals__', module)
    old_timeout = function_globals.get('PDF_PAGE_SCAN_TIMEOUT', 20.0)
    old_subprocess = function_globals.get('subprocess')
    old_pages = function_globals.get('_pdf_page_texts')
    if reader is None:
        function_globals['subprocess'] = _BoundedLocalRunner(data, deadline_monotonic or time.monotonic()+20)
    if remaining is not None:
        function_globals['PDF_PAGE_SCAN_TIMEOUT'] = min(float(old_timeout), max(0.01, remaining - 0.02))
    try:
        pages = module['_pdf_page_texts'](str(path))
        need(type(pages) is list and pages and all(type(page) is str for page in pages), 'PDF_PAGE_VIEW_UNAVAILABLE')
        need(any(page.strip() for page in pages), 'BLANK_PDF_TEXT')
        # Use the exact existing scoped page-view helper with the already local
        # page text as the unpaged payload. No anydoc/OCR route is entered.
        need(len(pages) <= 64 and sum(len(p.encode('utf-8')) for p in pages) <= 1_000_000, 'PDF_PAGE_TEXT_CAP')
        unpaged = '\n\f\n'.join(pages)
        # Reuse this same authoritative extraction in the existing formatter.
        # This avoids a second helper and a second shared timeout window.
        if reader is None:
            function_globals['_pdf_page_texts'] = lambda path: pages
        view = module['_pdf_scoped_page_view'](data, unpaged)
        need(type(view) is str and view.startswith(VIEW_HEADER), 'AUTHORITATIVE_PAGE_VIEW_REQUIRED')
        need('[end of page view' in view, 'TRUNCATED_OR_UNPAGED_PAGE_VIEW')
        for index, page in enumerate(pages, 1):
            need(not re.search(r'\[page [0-9]+\]|\[end of page view', page), 'PDF_SOURCE_DELIMITER_COLLISION')
            need(('[page %d]\n' % index) in view, 'PAGE_VIEW_SECTION_MISSING')
        return {'pages': pages, 'page_view': view, 'reader': {
            'source': {'path': str(READER), 'sha256': expected_sha256},
            'helper': tool, 'route': '_pdf_page_texts+_pdf_scoped_page_view',
            'ocr_or_hosted_fallback': False}}
    finally:
        if reader is None:
            function_globals['subprocess'] = old_subprocess
            function_globals['_pdf_page_texts'] = old_pages
        if remaining is not None:
            function_globals['PDF_PAGE_SCAN_TIMEOUT'] = old_timeout
