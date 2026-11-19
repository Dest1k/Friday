# Third-party notices

The Friday persona text in `config/SOUL.md` and its copy in the Hermes patch test fixture is adapted from the owner's existing Friday source at commit `cecd28a92ac4fd4e34c4d3813d0c598debe09436`. Its source license notice follows. This notice does not assign a new license to the entire integration repository.

## Friday source

MIT License

Copyright (c) 2026 Friday contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Hermes

The Hermes patches and Hermes-derived source copies/overlays in `analysis/2026-10-09/incremental-01` are based on pinned Hermes commit `781334eea4b9225a3e194faf0c241d9afe218634`. The upstream notice applies to those portions.

MIT License

Copyright (c) 2025 Nous Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## DeepSeek Harness

The Harness-derived TypeScript source/test copies and overlays in `analysis/2026-10-09/incremental-01` originate from commit `5badb15009ae1756c3afe0ae0cef1faafc290ccc`. Separately licensed native/system objects and upstream C copies are excluded from this subset. The upstream root notice follows.

MIT License

Copyright (c) 2026 DeepSeek

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Expanded analysis snapshot

The source copies and patches in `analysis/2026-10-09/incremental-02` retain their component licenses. See that snapshot's [component notices](analysis/2026-10-09/incremental-02/THIRD_PARTY_NOTICES.md), bundled license texts and upstream-source references. The repository's license does not replace those component terms.

## Ubuntu LibreOffice PyUNO

The DOCX to PDF native table-of-contents overlay carries four text-encoded members derived from Ubuntu `python3-uno` `4:26.2.5.2-0ubuntu0.26.04.1` for amd64. The binary package SHA-256 is `1444aac9366f765f1775fccbe87c54b41179bc8fdbfcb1b716d54efc7c2dd325`. The package notice applies to these members. [Ubuntu package notice](docs/dependencies/ubuntu-python3-uno-26.2.5.2-NOTICE.txt), [Ubuntu build 33476009](https://launchpad.net/ubuntu/+source/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/+build/33476009)

The two libraries and `unohelper.py` are exact package members. Friday relocates two paths in `uno.py` for the pinned, isolated Writer environment. The rest of the source and its notices are preserved.

```diff
--- Ubuntu/uno.py
+++ Friday/uno.py
@@ -1,4 +1,4 @@
 import sys, os
-sys.path.append('/usr/lib/libreoffice/program')
-os.putenv('URE_BOOTSTRAP', 'vnd.sun.star.pathname:/usr/lib/libreoffice/program/fundamentalrc')
+sys.path.append('/opt/friday-document-toolchain/root/usr/lib/libreoffice/program')
+os.putenv('URE_BOOTSTRAP', 'vnd.sun.star.pathname:/opt/friday-document-toolchain/root/usr/lib/libreoffice/program/fundamentalrc')
 # -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
```

Corresponding Ubuntu source files and checksums

- [libreoffice_26.2.5.2-0ubuntu0.26.04.1.dsc](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2-0ubuntu0.26.04.1.dsc), SHA-256 `7aff11c72d326919a7c680a30ea40fda8eea850880b8e393c5ae2d9e5714da4a`
- [libreoffice_26.2.5.2-0ubuntu0.26.04.1.debian.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2-0ubuntu0.26.04.1.debian.tar.xz), SHA-256 `8c71b61c17b65b9bccd6f565d7c6140df84ec6dd5a01d0f2930a8b6eead3a14f`
- [libreoffice_26.2.5.2.orig.tar.xz.asc](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig.tar.xz.asc), SHA-256 `7d7a6e0ef92640e455bd52f14cc7995b58950eb16905ca64e1e055e90e01bb7f`
- [libreoffice_26.2.5.2.orig.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig.tar.xz), SHA-256 `8ec785ee1fd1a1d9b9d8eba1c8ff7556695ca8f02e1f7a26bef8cd540f669fea`
- [libreoffice_26.2.5.2.orig-yaru.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig-yaru.tar.xz), SHA-256 `4ccde1789524f248438cea3f3ea24b0c7a1fb646879794ed263fe23fe98b66b3`
- [libreoffice_26.2.5.2.orig-translations.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig-translations.tar.xz), SHA-256 `6206bb90df4617cccbdae85db2486bc88fd30f2bca857cd1fb8749f5769c1a4a`
- [libreoffice_26.2.5.2.orig-tarballs.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig-tarballs.tar.xz), SHA-256 `aac56a5c67a5a9b4734bfbf2ec788d0b9ee758818add154abce795368369a8af`
- [libreoffice_26.2.5.2.orig-helpcontent2.tar.xz](https://launchpad.net/ubuntu/+archive/primary/+sourcefiles/libreoffice/4:26.2.5.2-0ubuntu0.26.04.1/libreoffice_26.2.5.2.orig-helpcontent2.tar.xz), SHA-256 `836610a1d5918a81adcc7243c7c863054d2c75feb58c68238306ef49f8509a0d`
