.hidden fixture_mode
.hidden fixture_repeat
.text
.globl fixture_native
.type fixture_native,@function
fixture_native:
.cfi_startproc
 mov (%rdi),%rax
 ret
.cfi_endproc
.size fixture_native,.-fixture_native
.globl fixture_outer
.type fixture_outer,@function
fixture_outer:
.cfi_startproc
 push %rbp
.cfi_def_cfa_offset 16
.cfi_offset %rbp,-16
 mov %rsp,%rbp
.cfi_def_cfa_register %rbp
 sub $32,%rsp
 mov %rdi,-8(%rbp)
 mov %rsi,-16(%rbp)
 cmpl $1,fixture_mode(%rip)
 je .Lmissing
.Lagain:
 mov -8(%rbp),%rax
 mov (%rax),%rdi
 mov -16(%rbp),%rsi
 xor %edx,%edx
 mov $-1,%ecx
 xor %r8d,%r8d
 xor %r9d,%r9d
 cmpl $3,fixture_mode(%rip)
 je .Lwrongcaller
 call fixture_native
.globl fixture_native_return_site
fixture_native_return_site:
 mov %eax,-20(%rbp)
 cmpl $2,fixture_mode(%rip)
 jne .Ldone
 cmpl $0,fixture_repeat(%rip)
 jne .Ldone
 movl $1,fixture_repeat(%rip)
 jmp .Lagain
.Ldone:
 mov -20(%rbp),%eax
 leave
.cfi_def_cfa %rsp,8
 ret
.Lwrongcaller:
.cfi_def_cfa %rbp,16
 call fixture_native
 jmp fixture_native_return_site
.Lmissing:
 xor %eax,%eax
 leave
.cfi_def_cfa %rsp,8
 ret
.cfi_endproc
.size fixture_outer,.-fixture_outer
.section .note.GNU-stack,"",@progbits
