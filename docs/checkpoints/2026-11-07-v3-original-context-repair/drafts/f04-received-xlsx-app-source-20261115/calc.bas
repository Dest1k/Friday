Option Explicit
Global observationOutput As Object
Global activeDoc As Object
Global activeOpen As Boolean
Global entries As Long, opens As Long, saves As Long, closes As Long
Global changes As Long, recalcs As Long
Global prefix As String

Sub Main
 Dim sfa As Object, stream As Object, filename, e As Long, failureLine As Long
 On Error GoTo Failed
 entries = entries + 1
 If entries <> 1 Then Guard 8101
 If ComponentCount() <> 0 Then Guard 8102
 sfa = CreateUnoService("com.sun.star.ucb.SimpleFileAccess")
 For Each filename In Array("observations.tsv", "journal.tsv", "controlledcopy-saved.xlsx", "saved-closed.tsv", "saved-closed.pending", "reopen-ready.tsv", "reopen-ready.pending", "complete.tsv")
  If sfa.exists(ConvertToURL("/work/" & filename)) Then Guard 8103
 Next filename
 stream = sfa.openFileWrite(ConvertToURL("/work/observations.tsv"))
 observationOutput = CreateUnoService("com.sun.star.io.TextOutputStream")
 observationOutput.setOutputStream(stream): observationOutput.setEncoding("UTF-8")
 Emit "BEGIN", "RECEIVED_DISPOSABLE_COPY_NOT_ORDINARY_OR_USER_DELIVERY"
 ProcessReceivedCopy
 If entries <> 1 Or opens <> 2 Or saves <> 1 Or closes <> 2 Or changes <> 1 Or recalcs <> 1 Or activeOpen Then Guard 8104
 If ComponentCount() <> 0 Then Guard 8105
 Emit "COUNTS", "1:2:1:2:1:1"
 Emit "COMPLETE", "RECEIVED_COPY_SAVED_CLOSED_REOPENED"
 Journal "COMPLETE", "1:2:1:2:1:1"
 observationOutput.closeOutput()
 WriteReceipt "complete.tsv", "COMPLETE" & Chr(9) & "1:2:1:2:1:1"
 StarDesktop.terminate()
 Exit Sub
Failed:
 e = Err: failureLine = Erl
 On Error Resume Next
 Journal "FAIL", CStr(e) & ":" & CStr(failureLine)
 Emit "FAIL", CStr(e) & ":" & CStr(failureLine)
 If activeOpen Then
  activeOpen = False
  activeDoc.close(True)
  Journal "FAIL_CLOSE", "ATTEMPTED_ONCE"
 End If
 observationOutput.closeOutput()
 StarDesktop.terminate()
End Sub

Sub ProcessReceivedCopy
 Dim cell As Object, props(1) As New com.sun.star.beans.PropertyValue
 Dim sfa As Object, ticks As Long, line As String, handle As Integer
 prefix = "RECEIVED_COPY_BASELINE"
 OpenCalc "/work/received-copy.xlsx", False, "Calc MS Excel 2007 XML"
 If activeDoc.getSheets().getCount() <> 3 Then Guard 8106
 If activeDoc.getSheets().getByIndex(0).getName() <> "Orders" Then Guard 8107
 ObserveWidths
 ObserveSelected
 cell = activeDoc.getSheets().getByIndex(0).getCellRangeByName("C2")
 If cell.getType() <> com.sun.star.table.CellContentType.VALUE Then Guard 8110
 If cell.getValue() <> 2 Then Guard 8114
 If changes >= 1 Then Guard 8111
 Journal "CHANGE_INTENT", "FIRST_SHEET:C2:2:PLUS_ONE:3"
 cell.setValue(cell.getValue() + 1)
 changes = changes + 1
 If cell.getType() <> com.sun.star.table.CellContentType.VALUE Or cell.getValue() <> 3 Then Guard 8115
 Journal "CHANGED", "FIRST_SHEET:C2:2:PLUS_ONE:3"
 If recalcs >= 1 Then Guard 8112
 Journal "CALCULATE_ALL_INTENT", "RECEIVED_COPY"
 activeDoc.calculateAll()
 recalcs = recalcs + 1
 Journal "CALCULATED_ALL", "RECEIVED_COPY"
 prefix = "CONTROLLED_COPY_BEFORE_SAVE"
 ObserveSelected
 sfa = CreateUnoService("com.sun.star.ucb.SimpleFileAccess")
 If sfa.exists(ConvertToURL("/work/controlledcopy-saved.xlsx")) Or saves >= 1 Then Guard 8113
 props(0).Name = "FilterName": props(0).Value = "Calc MS Excel 2007 XML"
 props(1).Name = "Overwrite": props(1).Value = False
 Journal "SAVE_INTENT", "controlledcopy-saved.xlsx"
 activeDoc.storeAsURL(ConvertToURL("/work/controlledcopy-saved.xlsx"), props())
 saves = saves + 1
 Journal "SAVED", "controlledcopy-saved.xlsx"
 CloseCalc "controlledcopy-saved.xlsx"
 If ComponentCount() <> 0 Then Guard 8116
 ' Publish only after WriteReceipt closed the complete pending file. The
 ' parent must never see a transient empty/truncated closed-save receipt.
 WriteReceipt "saved-closed.pending", "SAVED_CLOSED" & Chr(9) & "1:1:1:1:1:1"
 sfa.move(ConvertToURL("/work/saved-closed.pending"), ConvertToURL("/work/saved-closed.tsv"))
 ' The existing parent phase loop pins the closed new output before this open.
 ' 600 nominal Wait50 steps; the parent separately enforces its monotonic
 ' observation30, Main180 and work270 deadlines before atomic gate release.
 For ticks = 1 To 600
  If sfa.exists(ConvertToURL("/work/reopen-ready.tsv")) Then Exit For
  Wait 50
 Next ticks
 If ticks > 600 Then Guard 8117
 handle = FreeFile
 Open "/work/reopen-ready.tsv" For Input Access Read Lock Read As #handle
 Line Input #handle, line
 If Not EOF(handle) Then
  Close #handle
  Guard 8118
 End If
 Close #handle
 If line <> "REOPEN_AUTHORIZED_SAME_PINNED_NEW_OUTPUT" Then Guard 8119
 prefix = "CONTROLLED_COPY_READONLY_REOPENED"
 OpenCalc "/work/controlledcopy-saved.xlsx", True, "Calc MS Excel 2007 XML"
 ObserveWidths
 ObserveSelected
 CloseCalc "controlledcopy-saved.xlsx"
End Sub

Sub OpenCalc(path As String, readonlyFlag As Boolean, filter As String)
 Dim props(4) As New com.sun.star.beans.PropertyValue
 If activeOpen Or opens >= 2 Then Guard 8120
 If (opens = 0 And (path <> "/work/received-copy.xlsx" Or readonlyFlag)) Or (opens = 1 And (path <> "/work/controlledcopy-saved.xlsx" Or Not readonlyFlag)) Or filter <> "Calc MS Excel 2007 XML" Then Guard 8124
 props(0).Name = "Hidden": props(0).Value = True
 props(1).Name = "ReadOnly": props(1).Value = readonlyFlag
 props(2).Name = "MacroExecutionMode": props(2).Value = 0
 props(3).Name = "UpdateDocMode": props(3).Value = 0
 props(4).Name = "FilterName": props(4).Value = filter
 Journal "OPEN_INTENT", path
 activeDoc = StarDesktop.loadComponentFromURL(ConvertToURL(path), "_blank", 0, props())
 activeOpen = True: opens = opens + 1
 Journal "OPENED", path
 If Not activeDoc.supportsService("com.sun.star.sheet.SpreadsheetDocument") Then Guard 8121
 If activeDoc.isReadonly() <> readonlyFlag Then Guard 8122
 Emit "READ_ONLY", CStr(activeDoc.isReadonly())
End Sub

Sub CloseCalc(filename As String)
 If Not activeOpen Or closes >= 2 Then Guard 8123
 ' Attempt flag precedes close: an ambiguous failed close is never retried.
 activeOpen = False
 Journal "CLOSE_INTENT", filename
 activeDoc.close(True)
 closes = closes + 1
 Journal "CLOSED", filename
End Sub

Sub ObserveWidths
 Dim sheet As Object, col As Object, i As Long, s As Long
 If activeDoc.getSheets().getCount() <> 3 Then Guard 8125
 For s = 0 To 2
  sheet = activeDoc.getSheets().getByIndex(s)
  For i = 0 To 6
   col = sheet.getColumns().getByIndex(i)
   Emit "WIDTH:" & CStr(s) & ":" & CStr(i + 1), CStr(col.getPropertyValue("Width"))
   Emit "OPTIMAL_WIDTH:" & CStr(s) & ":" & CStr(i + 1), CStr(col.getPropertyValue("OptimalWidth"))
   Emit "COLUMN_VISIBLE:" & CStr(s) & ":" & CStr(i + 1), CStr(col.getPropertyValue("IsVisible"))
  Next i
 Next s
End Sub

Sub ObserveSelected
 Dim sheets As Object, sheet As Object, cell As Object, i As Long, row As Long, addr, kind As Long
 sheets = activeDoc.getSheets()
 If sheets.getCount() <> 3 Then Guard 8130
 Emit "SHEET_COUNT", CStr(sheets.getCount())
 For i = 0 To sheets.getCount() - 1
  Emit "SHEET_NAME:" & CStr(i), sheets.getByIndex(i).getName()
 Next i
 sheet = sheets.getByIndex(0)
 For row = 2 To 5
  For Each addr In Array("A" & CStr(row), "C" & CStr(row), "D" & CStr(row), "G" & CStr(row))
   cell = sheet.getCellRangeByName(addr)
   ObserveCell cell, "0:" & addr
  Next addr
 Next row
 cell = sheets.getByIndex(1).getCellRangeByName("B2")
 ObserveCell cell, "1:B2"
End Sub

Sub ObserveCell(cell As Object, key As String)
 Dim kind As Long
 kind = cell.getType()
 Emit "CELL_TYPE:" & key, CStr(kind)
 Emit "CELL_ERROR:" & key, CStr(cell.getError())
 If kind = com.sun.star.table.CellContentType.TEXT Then
  Emit "CELL_TEXT:" & key, cell.getString()
 ElseIf kind = com.sun.star.table.CellContentType.VALUE Then
  Emit "CELL_VALUE_CSTR:" & key, CStr(cell.getValue())
 ElseIf kind = com.sun.star.table.CellContentType.FORMULA Then
  Emit "CELL_FORMULA:" & key, cell.getFormula()
  Emit "CELL_VALUE_CSTR:" & key, CStr(cell.getValue())
 Else
  Guard 8131
 End If
End Sub

Function ComponentCount() As Long
 Dim iterator As Object, item As Object, n As Long
 iterator = StarDesktop.getComponents().createEnumeration()
 While iterator.hasMoreElements()
  item = iterator.nextElement(): n = n + 1
  If n > 8 Then Guard 8150
 Wend
 ComponentCount = n
End Function

Sub InitOnly
 Dim e As Long
 On Error GoTo Failed
 WriteReceipt "init-entered.tsv", "INIT_ONLY_ENTERED"
 If ComponentCount() <> 0 Then Guard 8151
 WriteReceipt "init-only.tsv", "INIT_ONLY" & Chr(9) & "COMPONENTS=0"
 StarDesktop.terminate()
 Exit Sub
Failed:
 e = Err
 On Error Resume Next
 WriteReceipt "init-failed.tsv", "FAIL" & Chr(9) & CStr(e)
 StarDesktop.terminate()
End Sub

Sub Guard(code As Long)
 Journal "GUARD", CStr(code)
 Error 5
End Sub

Sub Emit(key As String, ByVal value As String)
 value = Replace(value, "\", "\\")
 value = Replace(value, Chr(9), "\t")
 value = Replace(value, Chr(13), "\r")
 value = Replace(value, Chr(10), "\n")
 observationOutput.writeString(prefix & ":" & key & Chr(9) & value & Chr(10))
 observationOutput.flush()
End Sub

Sub Journal(key As String, value As String)
 Dim handle As Integer
 handle = FreeFile
 Open "/work/journal.tsv" For Append Access Write Lock Write As #handle
 Print #handle, key & Chr(9) & value
 Close #handle
End Sub

Sub WriteReceipt(filename As String, value As String)
 Dim handle As Integer
 handle = FreeFile
 Open "/work/" & filename For Output Access Write Lock Write As #handle
 Print #handle, value
 Close #handle
End Sub
