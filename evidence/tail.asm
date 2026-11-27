
/home/jiji/prefetch-indirect-pilot/tail-peel-20261127/tail:     file format elf64-x86-64


Disassembly of section .init:

Disassembly of section .plt:

Disassembly of section .plt.sec:

Disassembly of section .bolt.org.text:

Disassembly of section .fini:

Disassembly of section .text:

0000000000800700 <spmv>:
  800700:	f3 0f 1e fa          	endbr64 
  800704:	49 89 fa             	mov    %rdi,%r10
  800707:	48 85 ff             	test   %rdi,%rdi
  80070a:	0f 84 fe 01 00 00    	je     80090e <spmv.cold.0>
  800710:	53                   	push   %rbx
  800711:	49 89 f3             	mov    %rsi,%r11
  800714:	48 89 d7             	mov    %rdx,%rdi
  800717:	31 db                	xor    %ebx,%ebx
  800719:	c5 f1 57 c9          	vxorpd %xmm1,%xmm1,%xmm1
  80071d:	e9 bd 00 00 00       	jmp    8007df <spmv+0xdf>
  800722:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  800725:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  80072a:	48 83 c0 01          	add    $0x1,%rax
  80072e:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  800734:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  800737:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  80073c:	48 83 c0 01          	add    $0x1,%rax
  800740:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  800746:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  800749:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  80074e:	48 83 c0 01          	add    $0x1,%rax
  800752:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  800758:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  80075b:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  800760:	48 83 c0 01          	add    $0x1,%rax
  800764:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  80076a:	48 89 f2             	mov    %rsi,%rdx
  80076d:	48 29 c2             	sub    %rax,%rdx
  800770:	48 81 fa 04 00 00 00 	cmp    $0x4,%rdx
  800777:	77 a9                	ja     800722 <spmv+0x22>
  800779:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  80077c:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  800781:	48 83 c0 01          	add    $0x1,%rax
  800785:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  80078b:	48 39 f0             	cmp    %rsi,%rax
  80078e:	74 43                	je     8007d3 <spmv+0xd3>
  800790:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  800793:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  800798:	48 83 c0 01          	add    $0x1,%rax
  80079c:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  8007a2:	48 39 f0             	cmp    %rsi,%rax
  8007a5:	74 2c                	je     8007d3 <spmv+0xd3>
  8007a7:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  8007aa:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  8007af:	48 83 c0 01          	add    $0x1,%rax
  8007b3:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  8007b9:	48 39 f0             	cmp    %rsi,%rax
  8007bc:	74 15                	je     8007d3 <spmv+0xd3>
  8007be:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  8007c1:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  8007c6:	48 83 c0 01          	add    $0x1,%rax
  8007ca:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  8007d0:	48 39 f0             	cmp    %rsi,%rax
  8007d3:	c4 c1 7b 11 44 d9 f8 	vmovsd %xmm0,-0x8(%r9,%rbx,8)
  8007da:	49 39 da             	cmp    %rbx,%r10
  8007dd:	74 41                	je     800820 <spmv+0x120>
  8007df:	49 8b 04 db          	mov    (%r11,%rbx,8),%rax
  8007e3:	48 83 c3 01          	add    $0x1,%rbx
  8007e7:	c5 f3 10 c1          	vmovsd %xmm1,%xmm1,%xmm0
  8007eb:	49 8b 34 db          	mov    (%r11,%rbx,8),%rsi
  8007ef:	48 39 f0             	cmp    %rsi,%rax
  8007f2:	73 df                	jae    8007d3 <spmv+0xd3>
  8007f4:	48 89 f2             	mov    %rsi,%rdx
  8007f7:	48 29 c2             	sub    %rax,%rdx
  8007fa:	48 81 fa 10 00 00 00 	cmp    $0x10,%rdx
  800801:	0f 87 1b ff ff ff    	ja     800722 <spmv+0x22>
  800807:	8b 14 87             	mov    (%rdi,%rax,4),%edx
  80080a:	c5 fb 10 14 c1       	vmovsd (%rcx,%rax,8),%xmm2
  80080f:	48 83 c0 01          	add    $0x1,%rax
  800813:	c4 c2 e9 b9 04 d0    	vfmadd231sd (%r8,%rdx,8),%xmm2,%xmm0
  800819:	48 39 f0             	cmp    %rsi,%rax
  80081c:	75 e9                	jne    800807 <spmv+0x107>
  80081e:	eb b3                	jmp    8007d3 <spmv+0xd3>
  800820:	5b                   	pop    %rbx
  800821:	c3                   	ret    

Disassembly of section .text.cold:
