"""Write the TrueConf observer subset from the exact owner-supplied patched verifier."""

import argparse
import ast
import hashlib
from pathlib import Path
from textwrap import dedent, indent


STOCK_SHA256 = "7dd11e702677f50c9390ca078ab882baaa3d84140c432aed09106ccace45e851"
EXACT_IMPORTS = (
    "contextlib", "dt", "fcntl", "hashlib", "json", "os", "Path", "pwd", "re", "stat",
    "unicodedata",
)
EXACT_SYMBOLS = (
    "CANONICAL_STATE", "MAX_JSON", "MAX_FILE", "MAX_UPLOAD", "UPLOAD_TYPES",
    "INPUT_STAT_FIELDS", "Refused", "Uncertain", "stamp", "digest", "encoded", "no_symlinks",
    "secure_dir", "safe_read", "bounded_capture", "validate_capture", "verify_exact_document_bytes",
    "validate_document_input", "input_stat", "read_document_input", "Store", "unique_object",
)


def generate(data):
    if hashlib.sha256(data).hexdigest() != STOCK_SHA256:
        raise ValueError("Patched stock verifier SHA-256 mismatch")

    source = data.decode("utf-8")
    lines = source.splitlines(keepends=True)
    nodes = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.asname or alias.name for alias in node.names]
        elif isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            names = [node.name]
        else:
            names = []
        for name in names:
            nodes[name] = node

    def block(node):
        start = min((item.lineno for item in getattr(node, "decorator_list", [])), default=node.lineno)
        return "".join(lines[start - 1:node.end_lineno]).rstrip()

    # The TrueConf caller already limits accepted plans to a document and exact text.
    # Keep the ordinary branch and explicitly refuse stock-only capture modes.
    plan = block(nodes["validate_scenario_steps"])
    mode_start = plan.index("        if 'mode' in expected:\n")
    mode_end = plan.index("        if set(expected) -", mode_start)
    plan = (plan[:mode_start] + "        if 'mode' in expected:\n"
            "            raise Refused('Unsupported observation schema')\n" + plan[mode_end:])
    plan = plan.replace("                validate_capture(doc)\n                continue\n",
                        "                raise Refused('Unsupported document observation schema')\n", 1)

    # The caller supplies one two-key, explicitly named output. Keep its stock
    # catalogue check and single-document matching branch verbatim within that scope.
    output_check = block(nodes["ordinary_document_outputs"])
    declaration_start = output_check.index("        if (not isinstance(output, dict)")
    declaration_end = output_check.index("    explicit_names =")
    declaration = dedent(output_check[declaration_start:declaration_end])
    declaration = declaration.replace("(set(output) != {'filename', 'mime_type'} and not optional)",
                                      "set(output) != {'filename', 'mime_type'}", 1)
    output_match = block(nodes["ordinary_document_output_failures"])
    count_start = output_match.index("    if len(documents) != len(outputs):")
    match_start = output_match.index("    if len(outputs) == 1:", count_start)
    match_end = output_match.index("    expected = sorted(", match_start)
    count = output_match[count_start:match_start].replace("len(outputs)", "1", 1)
    match = output_match[match_start:match_end].split("\n", 1)[1]
    match = indent(dedent(match).replace("outputs[0]", "output"), "    ")
    response = ("def ordinary_document_response_failures(output, observations):\n"
                + indent(declaration, "    ") + "\n"
                + "    documents = [o for o in observations if o.get('kind') == 'document']\n"
                + count + match.rstrip())

    ready_node = next(node for node in nodes["Runner"].body
                      if isinstance(node, ast.FunctionDef) and node.name == "ready")
    ready = "def observation_ready(run):\n" + indent(
        dedent(block(ready_node.body[0]) + "\n" + block(ready_node.body[-1])), "    ")

    imports = "\n".join(block(nodes[name]) for name in EXACT_IMPORTS)
    header = ('"""Stock custody and ordinary document verification used by TrueConf.\n\n'
              'Reproduce from the owner-supplied verifier with packaging/extract_observer.py.\n'
              '"""')
    result = "\n\n\n".join([header, imports, *(block(nodes[name]) for name in EXACT_SYMBOLS),
                            plan, response, ready]) + "\n"
    compile(result, "_stock_observer.py", "exec")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock_observer", type=Path, help="exact patched stock Python source")
    args = parser.parse_args()
    try:
        result = generate(args.stock_observer.read_bytes())
    except ValueError as error:
        parser.error(str(error))
    print(result, end="")
