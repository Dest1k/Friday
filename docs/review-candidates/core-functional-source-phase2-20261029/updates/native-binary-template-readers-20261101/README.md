Binary Word and Excel template readers

These source-only changes repair two limitations exposed by real producer files. The XLT reader now returns the stored Sheet1!A1 value from an unchanged Microsoft Excel template retained in Apache Tika. It accepts a finite set of passive formatting records while keeping their payloads opaque, and handles bounded empty header/footer, page-layout and inactive protection metadata. It never executes formulas, opens the embedded theme archive, or instantiates a template.

The Word CFB reader no longer requires equal black depth in its directory tree. Microsoft CFB permits an unbalanced all-black tree; ordering, ownership, allocation, cycle and color checks remain. The genuine Word template now passes the container reader, then is correctly refused because it contains unsupported fields. This is not a successful full DOT text extraction.

The source changes passed local and independent checks. They are not yet incorporated into the next aggregate or installed; Source117 remains the operational version. No Office, Telegram or live user acceptance is claimed.

References: [MS-CFB directory tree](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/d30e462c-5f8a-435b-9c4c-cc0b9ea89956), [MS-XLS Globals](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/ca4c1748-8729-4a93-abb9-4602b3a01fb1), [FeatHdr](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-xls/5748f633-4a5c-4b2c-9f45-2d21c06f753d).
