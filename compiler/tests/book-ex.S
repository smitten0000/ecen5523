
.globl main
main:
	pushl %ebp
	movl %esp, %ebp
	subl $12,%esp # make stack space for variables

	# tmp0 = input()
	call input
	movl %eax, -4(%ebp)

	# tmp1 = - tmp0
	movl -4(%ebp), %eax
	negl %eax
	movl %eax, -8(%ebp)

	# tmp2 = tmp1 + 2
	movl -8(%ebp), %eax
	addl $2,%eax
	movl %eax, -12(%ebp)

	# print tmp2
	movl -12(%ebp), %eax
	pushl %eax
	call print_int_nl
	addl $4, %esp

	movl $0, %eax # put return value in eax
	leave
	ret

