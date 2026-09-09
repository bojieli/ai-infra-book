	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 26, 0	sdk_version 26, 2
	.section	__TEXT,__literal16,16byte_literals
	.p2align	4, 0x0                          ; -- Begin function main
lCPI0_0:
	.long	0                               ; 0x0
	.long	1                               ; 0x1
	.long	2                               ; 0x2
	.long	3                               ; 0x3
lCPI0_1:
	.long	4                               ; 0x4
	.long	5                               ; 0x5
	.long	6                               ; 0x6
	.long	7                               ; 0x7
	.section	__TEXT,__text,regular,pure_instructions
	.globl	_main
	.p2align	2
_main:                                  ; @main
	.cfi_startproc
; %bb.0:
	stp	d13, d12, [sp, #-144]!          ; 16-byte Folded Spill
	stp	d11, d10, [sp, #16]             ; 16-byte Folded Spill
	stp	d9, d8, [sp, #32]               ; 16-byte Folded Spill
	stp	x28, x27, [sp, #48]             ; 16-byte Folded Spill
	stp	x26, x25, [sp, #64]             ; 16-byte Folded Spill
	stp	x24, x23, [sp, #80]             ; 16-byte Folded Spill
	stp	x22, x21, [sp, #96]             ; 16-byte Folded Spill
	stp	x20, x19, [sp, #112]            ; 16-byte Folded Spill
	stp	x29, x30, [sp, #128]            ; 16-byte Folded Spill
	add	x29, sp, #128
	sub	sp, sp, #928
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	.cfi_offset b8, -104
	.cfi_offset b9, -112
	.cfi_offset b10, -120
	.cfi_offset b11, -128
	.cfi_offset b12, -136
	.cfi_offset b13, -144
Lloh0:
	adrp	x8, ___stack_chk_guard@GOTPAGE
Lloh1:
	ldr	x8, [x8, ___stack_chk_guard@GOTPAGEOFF]
Lloh2:
	ldr	x8, [x8]
	stur	x8, [x29, #-144]
	add	x19, sp, #272
	mov	w8, #9                          ; =0x9
	str	x8, [sp]
Lloh3:
	adrp	x0, l_.str.3@PAGE
Lloh4:
	add	x0, x0, l_.str.3@PAGEOFF
	bl	_printf
	mov	x10, #0                         ; =0x0
Lloh5:
	adrp	x23, l_.str.6@PAGE
Lloh6:
	add	x23, x23, l_.str.6@PAGEOFF
	add	x9, x19, #136
	str	x9, [sp, #72]                   ; 8-byte Folded Spill
	mov	w20, #63489                     ; =0xf801
	movk	w20, #63, lsl #16
	movi	d8, #0000000000000000
	fmov	d9, #10.00000000
LBB0_1:                                 ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB0_4 Depth 2
                                        ;     Child Loop BB0_8 Depth 2
                                        ;     Child Loop BB0_42 Depth 2
                                        ;       Child Loop BB0_46 Depth 3
                                        ;         Child Loop BB0_47 Depth 4
                                        ;       Child Loop BB0_50 Depth 3
                                        ;       Child Loop BB0_54 Depth 3
                                        ;       Child Loop BB0_57 Depth 3
                                        ;     Child Loop BB0_15 Depth 2
                                        ;       Child Loop BB0_16 Depth 3
                                        ;     Child Loop BB0_21 Depth 2
                                        ;       Child Loop BB0_24 Depth 3
                                        ;     Child Loop BB0_31 Depth 2
                                        ;       Child Loop BB0_33 Depth 3
                                        ;         Child Loop BB0_35 Depth 4
                                        ;     Child Loop BB0_37 Depth 2
	stp	x23, x10, [sp, #80]             ; 16-byte Folded Spill
	mov	w8, #12                         ; =0xc
Lloh7:
	adrp	x9, l___const.main.shapes@PAGE
Lloh8:
	add	x9, x9, l___const.main.shapes@PAGEOFF
	madd	x8, x10, x8, x9
	ldpsw	x23, x24, [x8]
	ldrsw	x25, [x8, #8]
	lsl	x19, x23, #2
	mul	x0, x19, x24
	bl	_malloc
	mov	x27, x0
	smull	x8, w24, w25
	lsl	x0, x8, #2
	bl	_malloc
	mov	x28, x0
	mul	x0, x19, x25
	bl	_malloc
	mov	x19, x0
	smull	x8, w23, w25
	lsl	x0, x8, #3
	bl	_malloc
	cmp	x27, #0
	ccmp	x28, #0, #4, ne
	ccmp	x19, #0, #4, ne
	ccmp	x0, #0, #4, ne
	b.eq	LBB0_58
; %bb.2:                                ;   in Loop: Header=BB0_1 Depth=1
	mov	x21, x0
	str	x19, [sp, #144]                 ; 8-byte Folded Spill
	mul	w9, w24, w23
Lloh9:
	adrp	x8, _state@PAGE
Lloh10:
	ldr	w8, [x8, _state@PAGEOFF]
	cmp	w9, #1
	b.lt	LBB0_6
; %bb.3:                                ;   in Loop: Header=BB0_1 Depth=1
	mov	x10, x27
LBB0_4:                                 ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	umull	x11, w8, w20
	lsr	x11, x11, #33
	add	w11, w11, w11, lsl #11
	sub	w11, w8, w11
	sub	w11, w11, #1024
	scvtf	s0, w11, #10
	str	s0, [x10], #4
	subs	x9, x9, #1
	b.ne	LBB0_4
; %bb.5:                                ;   in Loop: Header=BB0_1 Depth=1
	adrp	x9, _state@PAGE
	str	w8, [x9, _state@PAGEOFF]
LBB0_6:                                 ;   in Loop: Header=BB0_1 Depth=1
	mul	w9, w25, w24
	cmp	w9, #1
	b.lt	LBB0_10
; %bb.7:                                ;   in Loop: Header=BB0_1 Depth=1
	mov	x10, x28
LBB0_8:                                 ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	umull	x11, w8, w20
	lsr	x11, x11, #33
	add	w11, w11, w11, lsl #11
	sub	w11, w8, w11
	sub	w11, w11, #1024
	scvtf	s0, w11, #10
	str	s0, [x10], #4
	subs	x9, x9, #1
	b.ne	LBB0_8
; %bb.9:                                ;   in Loop: Header=BB0_1 Depth=1
	adrp	x9, _state@PAGE
	str	w8, [x9, _state@PAGEOFF]
LBB0_10:                                ;   in Loop: Header=BB0_1 Depth=1
	cmp	w23, #1
	b.lt	LBB0_19
; %bb.11:                               ;   in Loop: Header=BB0_1 Depth=1
	cmp	w25, #1
	b.lt	LBB0_19
; %bb.12:                               ;   in Loop: Header=BB0_1 Depth=1
	cmp	w24, #0
	b.le	LBB0_18
; %bb.13:                               ;   in Loop: Header=BB0_1 Depth=1
	cmp	w24, #1
	b.ne	LBB0_39
; %bb.14:                               ;   in Loop: Header=BB0_1 Depth=1
	mov	x8, #0                          ; =0x0
	lsl	x9, x25, #3
	mov	x10, x21
LBB0_15:                                ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB0_16 Depth 3
	mul	x11, x8, x24
	ldr	s0, [x27, x11, lsl #2]
	fcvt	d0, s0
	mov	x11, x28
	mov	x12, x10
	mov	x13, x25
LBB0_16:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_15 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	s1, [x11], #4
	fcvt	d1, s1
	fmul	d1, d0, d1
	fadd	d1, d1, d8
	str	d1, [x12], #8
	subs	x13, x13, #1
	b.ne	LBB0_16
; %bb.17:                               ;   in Loop: Header=BB0_15 Depth=2
	add	x8, x8, #1
	add	x10, x10, x9
	cmp	x8, x23
	b.ne	LBB0_15
	b	LBB0_19
LBB0_18:                                ;   in Loop: Header=BB0_1 Depth=1
	smull	x8, w25, w23
	lsl	x1, x8, #3
	mov	x0, x21
	bl	_bzero
LBB0_19:                                ;   in Loop: Header=BB0_1 Depth=1
	mov	x22, #0                         ; =0x0
	mov	w19, #0                         ; =0x0
	mul	w8, w25, w23
	str	x8, [sp, #152]                  ; 8-byte Folded Spill
	str	x21, [sp, #96]                  ; 8-byte Folded Spill
	b	LBB0_21
LBB0_20:                                ;   in Loop: Header=BB0_21 Depth=2
	mov	x0, x27
	mov	x1, x28
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	mov	x19, x2
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	add	x1, sp, #208
	mov	w0, #6                          ; =0x6
	bl	_clock_gettime
	ldp	d11, d0, [sp, #208]
	scvtf	d0, d0
	mov	x8, #54933                      ; =0xd695
	movk	x8, #59430, lsl #16
	movk	x8, #11787, lsl #32
	movk	x8, #15889, lsl #48
	fmov	d10, x8
	fmul	d12, d0, d10
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	mov	x0, x27
	mov	x1, x28
	mov	x2, x19
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	blr	x26
	scvtf	d0, d11
	fadd	d11, d12, d0
	add	x1, sp, #208
	mov	w0, #6                          ; =0x6
	bl	_clock_gettime
	ldp	d0, d1, [sp, #208]
	scvtf	d0, d0
	scvtf	d1, d1
	fmul	d1, d1, d10
	fadd	d0, d1, d0
	fsub	d0, d0, d11
	fdiv	d0, d0, d9
	mov	x8, #7864                       ; =0x1eb8
	movk	x8, #60293, lsl #16
	movk	x8, #47185, lsl #32
	movk	x8, #16270, lsl #48
	fmov	d1, x8
	fdiv	d0, d1, d0
	fcvtzs	w8, d0
	cmp	w8, #1
	csinc	w8, w8, wzr, gt
	mov	w9, #10000                      ; =0x2710
	cmp	w8, w9
	csel	w8, w8, w9, lt
	add	x9, sp, #240
	str	w8, [x9, x22, lsl #2]
	cmp	x22, #6
	add	x8, x22, #1
	cset	w19, hi
	mov	x22, x8
	cmp	x8, #8
	b.eq	LBB0_29
LBB0_21:                                ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB0_24 Depth 3
	mov	w8, #24                         ; =0x18
Lloh11:
	adrp	x9, l___const.main.methods@PAGE
Lloh12:
	add	x9, x9, l___const.main.methods@PAGEOFF
	madd	x8, x22, x8, x9
	ldr	x9, [x8, #8]
	ldr	w20, [x8, #16]
	mov	x0, x27
	mov	x1, x28
	ldr	x21, [sp, #144]                 ; 8-byte Folded Reload
	mov	x2, x21
	mov	x3, x23
	mov	x4, x24
	mov	x5, x25
	mov	x6, x20
	mov	x26, x9
	blr	x9
	mov	x2, x21
	ldr	x21, [sp, #96]                  ; 8-byte Folded Reload
	sub	x11, x29, #208
	str	xzr, [x11, x22, lsl #3]
	ldr	x8, [sp, #152]                  ; 8-byte Folded Reload
	cmp	w8, #1
	mov	x10, #17197                     ; =0x432d
	movk	x10, #60188, lsl #16
	movk	x10, #14050, lsl #32
	movk	x10, #16154, lsl #48
	mov	w12, #2139095039                ; =0x7f7fffff
	mov	x13, #26865                     ; =0x68f1
	movk	x13, #35043, lsl #16
	movk	x13, #63669, lsl #32
	movk	x13, #16100, lsl #48
	b.lt	LBB0_20
; %bb.22:                               ;   in Loop: Header=BB0_21 Depth=2
	mov	x8, #0                          ; =0x0
	movi	d0, #0000000000000000
	b	LBB0_24
LBB0_23:                                ;   in Loop: Header=BB0_24 Depth=3
	add	x8, x8, #1
	ldr	x9, [sp, #152]                  ; 8-byte Folded Reload
	cmp	x9, x8
	b.eq	LBB0_20
LBB0_24:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_21 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	s1, [x2, x8, lsl #2]
	fmov	w9, s1
	and	w9, w9, #0x7fffffff
	cmp	w9, w12
	b.gt	LBB0_28
; %bb.25:                               ;   in Loop: Header=BB0_24 Depth=3
	fcvt	d1, s1
	ldr	d2, [x21, x8, lsl #3]
	fabd	d1, d1, d2
	fabs	d2, d2
	fmov	d3, x13
	fmul	d2, d2, d3
	fmov	d3, x10
	fadd	d2, d2, d3
	fcmp	d1, d2
	b.gt	LBB0_28
; %bb.26:                               ;   in Loop: Header=BB0_24 Depth=3
	fcmp	d1, d0
	b.le	LBB0_23
; %bb.27:                               ;   in Loop: Header=BB0_24 Depth=3
	str	d1, [x11, x22, lsl #3]
	fmov	d0, d1
	b	LBB0_23
LBB0_28:                                ;   in Loop: Header=BB0_1 Depth=1
Lloh13:
	adrp	x9, ___stderrp@GOTPAGE
Lloh14:
	ldr	x9, [x9, ___stderrp@GOTPAGEOFF]
Lloh15:
	ldr	x0, [x9]
	stp	x22, x8, [sp, #8]
	ldr	x8, [sp, #88]                   ; 8-byte Folded Reload
	str	x8, [sp]
Lloh16:
	adrp	x1, l_.str.4@PAGE
Lloh17:
	add	x1, x1, l_.str.4@PAGEOFF
	bl	_fprintf
	tbz	w19, #0, LBB0_60
LBB0_29:                                ;   in Loop: Header=BB0_1 Depth=1
	stp	x28, x27, [sp, #104]            ; 16-byte Folded Spill
	stp	x25, x24, [sp, #120]            ; 16-byte Folded Spill
	str	x23, [sp, #136]                 ; 8-byte Folded Spill
	mov	x15, #0                         ; =0x0
	add	x26, sp, #240
	b	LBB0_31
LBB0_30:                                ;   in Loop: Header=BB0_31 Depth=2
	add	x15, x15, #1
	cmp	x15, #9
	b.eq	LBB0_36
LBB0_31:                                ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB0_33 Depth 3
                                        ;         Child Loop BB0_35 Depth 4
	mov	x16, #0                         ; =0x0
Lloh18:
	adrp	x8, lCPI0_0@PAGE
Lloh19:
	ldr	q0, [x8, lCPI0_0@PAGEOFF]
Lloh20:
	adrp	x8, lCPI0_1@PAGE
Lloh21:
	ldr	q1, [x8, lCPI0_1@PAGEOFF]
	stp	q0, q1, [sp, #208]
	adrp	x12, _state@PAGE
	ldr	w8, [x12, _state@PAGEOFF]
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w9, w8, w8, lsl #5
	and	w8, w8, #0x7
	add	x13, sp, #208
	ldr	w10, [x13, w8, uxtw #2]
	str	w10, [sp, #236]
	mov	w10, #7                         ; =0x7
	str	w10, [x13, w8, uxtw #2]
	eor	w8, w9, w9, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	mov	w9, #18725                      ; =0x4925
	movk	w9, #9362, lsl #16
	umull	x9, w8, w9
	lsr	x9, x9, #32
	sub	w10, w8, w9
	add	w9, w9, w10, lsr #1
	lsr	w9, w9, #2
	sub	w9, w9, w9, lsl #3
	add	w9, w8, w9
	ldr	w10, [sp, #232]
	ldr	w11, [x13, w9, uxtw #2]
	str	w11, [sp, #232]
	str	w10, [x13, w9, uxtw #2]
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	mov	w14, #43691                     ; =0xaaab
	movk	w14, #43690, lsl #16
	umull	x9, w8, w14
	lsr	x9, x9, #34
	mov	w10, #6                         ; =0x6
	msub	w9, w9, w10, w8
	ldr	w10, [sp, #228]
	ldr	w11, [x13, w9, uxtw #2]
	str	w11, [sp, #228]
	str	w10, [x13, w9, uxtw #2]
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	mov	w9, #52429                      ; =0xcccd
	movk	w9, #52428, lsl #16
	umull	x9, w8, w9
	lsr	x9, x9, #34
	add	w9, w9, w9, lsl #2
	sub	w9, w8, w9
	ldr	w10, [x13, w9, uxtw #2]
	ldr	w11, [sp, #224]
	str	w10, [sp, #224]
	str	w11, [x13, w9, uxtw #2]
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w9, w8, w8, lsl #5
	and	w8, w8, #0x3
	ldr	w10, [sp, #220]
	orr	x8, x13, x8, lsl #2
	ldr	w11, [x8]
	str	w11, [sp, #220]
	str	w10, [x8]
	eor	w8, w9, w9, lsl #13
	eor	w8, w8, w8, lsr #17
	eor	w8, w8, w8, lsl #5
	umull	x9, w8, w14
	lsr	x9, x9, #33
	add	w9, w9, w9, lsl #1
	sub	w9, w8, w9
	ldr	w10, [sp, #216]
	orr	x9, x13, x9, lsl #2
	ldr	w11, [x9]
	str	w11, [sp, #216]
	str	w10, [x9]
	eor	w8, w8, w8, lsl #13
	eor	w8, w8, w8, lsr #17
	and	w9, w8, #0x1
	ldr	w10, [sp, #212]
	orr	x9, x13, x9, lsl #2
	ldr	w11, [x9]
	str	w11, [sp, #212]
	eor	w8, w8, w8, lsl #5
	str	w10, [x9]
	str	w8, [x12, _state@PAGEOFF]
	mov	w8, #107                        ; =0x6b
	mul	w8, w15, w8
	str	w8, [sp, #164]                  ; 4-byte Folded Spill
	str	x15, [sp, #168]                 ; 8-byte Folded Spill
	b	LBB0_33
LBB0_32:                                ;   in Loop: Header=BB0_33 Depth=3
	scvtf	d0, d10
	scvtf	d1, d11
	mov	x8, #54933                      ; =0xd695
	movk	x8, #59430, lsl #16
	movk	x8, #11787, lsl #32
	movk	x8, #15889, lsl #48
	fmov	d10, x8
	fmul	d1, d1, d10
	fadd	d11, d1, d0
	add	x1, sp, #192
	mov	w0, #6                          ; =0x6
	bl	_clock_gettime
	ldp	d0, d1, [sp, #192]
	scvtf	d0, d0
	scvtf	d1, d1
	fmul	d1, d1, d10
	fadd	d0, d1, d0
	fsub	d0, d0, d11
	mov	x8, #145685290680320            ; =0x848000000000
	movk	x8, #16686, lsl #48
	fmov	d1, x8
	fmul	d0, d0, d1
	scvtf	d1, w25
	fdiv	d0, d0, d1
	add	x8, sp, #272
	mov	w9, #72                         ; =0x48
	ldp	x16, x10, [sp, #176]            ; 16-byte Folded Reload
	smaddl	x8, w10, w9, x8
	ldr	x15, [sp, #168]                 ; 8-byte Folded Reload
	str	d0, [x8, x15, lsl #3]
	ldr	x9, [sp, #152]                  ; 8-byte Folded Reload
	ldr	w10, [sp, #164]                 ; 4-byte Folded Reload
	sdiv	w8, w10, w9
	msub	w8, w8, w9, w10
	ldr	s0, [x21, w8, uxtw #2]
	fcvt	d0, s0
	adrp	x8, _sink@PAGE
	ldr	d1, [x8, _sink@PAGEOFF]
	fadd	d0, d1, d0
	str	d0, [x8, _sink@PAGEOFF]
	add	x16, x16, #1
	cmp	x16, #8
	add	x26, sp, #240
	b.eq	LBB0_30
LBB0_33:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_31 Depth=2
                                        ; =>    This Loop Header: Depth=3
                                        ;         Child Loop BB0_35 Depth 4
	add	x8, sp, #208
	str	x16, [sp, #176]                 ; 8-byte Folded Spill
	ldrsw	x19, [x8, x16, lsl #2]
	add	x1, sp, #192
	mov	w0, #6                          ; =0x6
	bl	_clock_gettime
	ldp	d10, d11, [sp, #192]
	str	x19, [sp, #184]                 ; 8-byte Folded Spill
	ldr	w25, [x26, x19, lsl #2]
	cmp	w25, #1
	ldp	x27, x24, [sp, #128]            ; 16-byte Folded Reload
	ldp	x28, x22, [sp, #112]            ; 16-byte Folded Reload
	ldr	x19, [sp, #104]                 ; 8-byte Folded Reload
	ldr	x21, [sp, #144]                 ; 8-byte Folded Reload
	b.lt	LBB0_32
; %bb.34:                               ;   in Loop: Header=BB0_33 Depth=3
	mov	w8, #24                         ; =0x18
Lloh22:
	adrp	x9, l___const.main.methods@PAGE
Lloh23:
	add	x9, x9, l___const.main.methods@PAGEOFF
	ldr	x10, [sp, #184]                 ; 8-byte Folded Reload
	smaddl	x8, w10, w8, x9
	ldr	x26, [x8, #8]
	ldr	w20, [x8, #16]
	mov	x23, x25
LBB0_35:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_31 Depth=2
                                        ;       Parent Loop BB0_33 Depth=3
                                        ; =>      This Inner Loop Header: Depth=4
	mov	x0, x28
	mov	x1, x19
	mov	x2, x21
	mov	x3, x24
	mov	x4, x27
	mov	x5, x22
	mov	x6, x20
	blr	x26
	subs	w23, w23, #1
	b.ne	LBB0_35
	b	LBB0_32
LBB0_36:                                ;   in Loop: Header=BB0_1 Depth=1
	ldur	d0, [x29, #-208]
	ldr	w8, [sp, #240]
	str	d0, [sp, #56]
	stp	xzr, x8, [sp, #40]
Lloh24:
	adrp	x8, l_.str@PAGE
Lloh25:
	add	x9, x8, l_.str@PAGEOFF
	ldp	x8, x27, [sp, #120]             ; 16-byte Folded Reload
	mov	x28, x8
	stp	x8, x9, [sp, #24]
	ldr	x24, [sp, #136]                 ; 8-byte Folded Reload
	stp	x24, x27, [sp, #8]
	ldr	x8, [sp, #80]                   ; 8-byte Folded Reload
	str	x8, [sp]
Lloh26:
	adrp	x0, l_.str.5@PAGE
Lloh27:
	add	x0, x0, l_.str.5@PAGEOFF
	bl	_printf
	ldr	d0, [sp, #272]
	str	d0, [sp, #8]
Lloh28:
	adrp	x22, l_.str.6@PAGE
Lloh29:
	add	x22, x22, l_.str.6@PAGEOFF
	str	x22, [sp]
Lloh30:
	adrp	x25, l_.str.8@PAGE
Lloh31:
	add	x25, x25, l_.str.8@PAGEOFF
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #280]
	str	d0, [sp, #8]
Lloh32:
	adrp	x22, l_.str.9@PAGE
Lloh33:
	add	x22, x22, l_.str.9@PAGEOFF
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #288]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #296]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #304]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #312]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #320]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #328]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [sp, #336]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
Lloh34:
	adrp	x0, l_.str.10@PAGE
Lloh35:
	add	x0, x0, l_.str.10@PAGEOFF
	bl	_printf
	mov	x19, #0                         ; =0x0
	ldr	x20, [sp, #72]                  ; 8-byte Folded Reload
	mov	w21, #1                         ; =0x1
Lloh36:
	adrp	x23, l_.str.7@PAGE
Lloh37:
	add	x23, x23, l_.str.7@PAGEOFF
LBB0_37:                                ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
Lloh38:
	adrp	x8, l___const.main.methods@PAGE
Lloh39:
	add	x8, x8, l___const.main.methods@PAGEOFF
	add	x8, x8, x19
	ldr	x9, [x8, #24]
	sub	x10, x29, #208
	ldr	d0, [x10, x21, lsl #3]
	ldr	w10, [x26, x21, lsl #2]
	str	d0, [sp, #56]
	str	x10, [sp, #48]
	ldr	w8, [x8, #40]
	stp	x9, x8, [sp, #32]
	stp	x27, x28, [sp, #16]
	stp	x23, x24, [sp]
Lloh40:
	adrp	x0, l_.str.5@PAGE
Lloh41:
	add	x0, x0, l_.str.5@PAGEOFF
	bl	_printf
	ldur	d0, [x20, #-64]
	str	d0, [sp, #8]
Lloh42:
	adrp	x8, l_.str.6@PAGE
Lloh43:
	add	x8, x8, l_.str.6@PAGEOFF
	str	x8, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-56]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-48]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-40]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-32]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-24]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-16]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldur	d0, [x20, #-8]
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
	ldr	d0, [x20], #72
	str	d0, [sp, #8]
	str	x22, [sp]
	mov	x0, x25
	bl	_printf
Lloh44:
	adrp	x0, l_.str.10@PAGE
Lloh45:
	add	x0, x0, l_.str.10@PAGEOFF
	bl	_printf
	add	x21, x21, #1
	add	x19, x19, #24
	cmp	x19, #168
	b.ne	LBB0_37
; %bb.38:                               ;   in Loop: Header=BB0_1 Depth=1
	ldr	x0, [sp, #112]                  ; 8-byte Folded Reload
	bl	_free
	ldr	x0, [sp, #104]                  ; 8-byte Folded Reload
	bl	_free
	ldr	x0, [sp, #144]                  ; 8-byte Folded Reload
	bl	_free
	ldr	x0, [sp, #96]                   ; 8-byte Folded Reload
	bl	_free
	ldr	x10, [sp, #88]                  ; 8-byte Folded Reload
	add	x10, x10, #1
	cmp	x10, #4
	mov	w20, #63489                     ; =0xf801
	movk	w20, #63, lsl #16
	b.ne	LBB0_1
	b	LBB0_59
LBB0_39:                                ;   in Loop: Header=BB0_1 Depth=1
	mov	x8, #0                          ; =0x0
	and	x9, x24, #0x7ffffff0
	and	x10, x24, #0xe
	and	x11, x24, #0x7ffffffe
	lsl	x12, x24, #2
	lsl	x13, x25, #2
	add	x14, x27, #32
	add	x15, x28, #32
	neg	x16, x11
	mov	x17, x27
	b	LBB0_42
LBB0_40:                                ;   in Loop: Header=BB0_42 Depth=2
	str	d0, [x0]
LBB0_41:                                ;   in Loop: Header=BB0_42 Depth=2
	add	x8, x8, #1
	add	x17, x17, x12
	add	x14, x14, x12
	cmp	x8, x23
	b.eq	LBB0_19
LBB0_42:                                ;   Parent Loop BB0_1 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB0_46 Depth 3
                                        ;         Child Loop BB0_47 Depth 4
                                        ;       Child Loop BB0_50 Depth 3
                                        ;       Child Loop BB0_54 Depth 3
                                        ;       Child Loop BB0_57 Depth 3
	mul	x0, x8, x25
	add	x0, x21, x0, lsl #3
	cmp	w25, #1
	b.ne	LBB0_45
; %bb.43:                               ;   in Loop: Header=BB0_42 Depth=2
	cmp	w24, #16
	b.hs	LBB0_49
; %bb.44:                               ;   in Loop: Header=BB0_42 Depth=2
	mov	x2, #0                          ; =0x0
	movi	d0, #0000000000000000
	b	LBB0_53
LBB0_45:                                ;   in Loop: Header=BB0_42 Depth=2
	mov	x1, #0                          ; =0x0
	mov	x2, x28
LBB0_46:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_42 Depth=2
                                        ; =>    This Loop Header: Depth=3
                                        ;         Child Loop BB0_47 Depth 4
	movi	d0, #0000000000000000
	mov	x3, x24
	mov	x4, x2
	mov	x5, x17
LBB0_47:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_42 Depth=2
                                        ;       Parent Loop BB0_46 Depth=3
                                        ; =>      This Inner Loop Header: Depth=4
	ldr	s1, [x5], #4
	fcvt	d1, s1
	ldr	s2, [x4]
	fcvt	d2, s2
	fmul	d1, d1, d2
	fadd	d0, d0, d1
	add	x4, x4, x13
	subs	x3, x3, #1
	b.ne	LBB0_47
; %bb.48:                               ;   in Loop: Header=BB0_46 Depth=3
	str	d0, [x0, x1, lsl #3]
	add	x1, x1, #1
	add	x2, x2, #4
	cmp	x1, x25
	b.ne	LBB0_46
	b	LBB0_41
LBB0_49:                                ;   in Loop: Header=BB0_42 Depth=2
	movi	d0, #0000000000000000
	mov	x1, x15
	mov	x2, x14
	mov	x3, x9
LBB0_50:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_42 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldp	q1, q2, [x2, #-32]
	ldp	q3, q4, [x2], #64
	fcvtl	v5.2d, v1.2s
	fcvtl2	v1.2d, v1.4s
	fcvtl	v6.2d, v2.2s
	fcvtl2	v2.2d, v2.4s
	fcvtl	v7.2d, v3.2s
	fcvtl2	v3.2d, v3.4s
	fcvtl	v16.2d, v4.2s
	fcvtl2	v4.2d, v4.4s
	ldp	q17, q18, [x1, #-32]
	ldp	q19, q20, [x1], #64
	fcvtl	v21.2d, v17.2s
	fcvtl2	v17.2d, v17.4s
	fcvtl	v22.2d, v18.2s
	fcvtl2	v18.2d, v18.4s
	fcvtl	v23.2d, v19.2s
	fcvtl2	v19.2d, v19.4s
	fcvtl	v24.2d, v20.2s
	fcvtl2	v20.2d, v20.4s
	fmul.2d	v1, v1, v17
	mov	d17, v1[1]
	fmul.2d	v5, v5, v21
	mov	d21, v5[1]
	fmul.2d	v2, v2, v18
	mov	d18, v2[1]
	fmul.2d	v6, v6, v22
	mov	d22, v6[1]
	fmul.2d	v3, v3, v19
	mov	d19, v3[1]
	fmul.2d	v7, v7, v23
	mov	d23, v7[1]
	fmul.2d	v4, v4, v20
	mov	d20, v4[1]
	fmul.2d	v16, v16, v24
	mov	d24, v16[1]
	fadd	d0, d0, d5
	fadd	d0, d0, d21
	fadd	d0, d0, d1
	fadd	d0, d0, d17
	fadd	d0, d0, d6
	fadd	d0, d0, d22
	fadd	d0, d0, d2
	fadd	d0, d0, d18
	fadd	d0, d0, d7
	fadd	d0, d0, d23
	fadd	d0, d0, d3
	fadd	d0, d0, d19
	fadd	d0, d0, d16
	fadd	d0, d0, d24
	fadd	d0, d0, d4
	fadd	d0, d0, d20
	subs	x3, x3, #16
	b.ne	LBB0_50
; %bb.51:                               ;   in Loop: Header=BB0_42 Depth=2
	cmp	x9, x24
	b.eq	LBB0_40
; %bb.52:                               ;   in Loop: Header=BB0_42 Depth=2
	mov	x1, x9
	mov	x2, x9
	cbz	x10, LBB0_56
LBB0_53:                                ;   in Loop: Header=BB0_42 Depth=2
	add	x1, x16, x2
	lsl	x2, x2, #2
LBB0_54:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_42 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	d1, [x17, x2]
	fcvtl	v1.2d, v1.2s
	ldr	d2, [x28, x2]
	fcvtl	v2.2d, v2.2s
	fmul.2d	v1, v1, v2
	mov	d2, v1[1]
	fadd	d0, d0, d1
	fadd	d0, d0, d2
	add	x2, x2, #8
	adds	x1, x1, #2
	b.ne	LBB0_54
; %bb.55:                               ;   in Loop: Header=BB0_42 Depth=2
	mov	x1, x11
	cmp	x11, x24
	b.eq	LBB0_40
LBB0_56:                                ;   in Loop: Header=BB0_42 Depth=2
	madd	x2, x13, x1, x28
LBB0_57:                                ;   Parent Loop BB0_1 Depth=1
                                        ;     Parent Loop BB0_42 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	s1, [x17, x1, lsl #2]
	fcvt	d1, s1
	ldr	s2, [x2]
	fcvt	d2, s2
	fmul	d1, d1, d2
	fadd	d0, d0, d1
	add	x1, x1, #1
	add	x2, x2, x13
	cmp	x24, x1
	b.ne	LBB0_57
	b	LBB0_40
LBB0_58:
	mov	w0, #2                          ; =0x2
	b	LBB0_61
LBB0_59:
Lloh46:
	adrp	x8, _sink@PAGE
Lloh47:
	ldr	d0, [x8, _sink@PAGEOFF]
	str	d0, [sp]
Lloh48:
	adrp	x0, l_.str.11@PAGE
Lloh49:
	add	x0, x0, l_.str.11@PAGEOFF
	bl	_printf
	mov	w0, #0                          ; =0x0
	b	LBB0_61
LBB0_60:
	mov	w0, #3                          ; =0x3
LBB0_61:
	ldur	x8, [x29, #-144]
Lloh50:
	adrp	x9, ___stack_chk_guard@GOTPAGE
Lloh51:
	ldr	x9, [x9, ___stack_chk_guard@GOTPAGEOFF]
Lloh52:
	ldr	x9, [x9]
	cmp	x9, x8
	b.ne	LBB0_63
; %bb.62:
	add	sp, sp, #928
	ldp	x29, x30, [sp, #128]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #112]            ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #96]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #80]             ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #64]             ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #48]             ; 16-byte Folded Reload
	ldp	d9, d8, [sp, #32]               ; 16-byte Folded Reload
	ldp	d11, d10, [sp, #16]             ; 16-byte Folded Reload
	ldp	d13, d12, [sp], #144            ; 16-byte Folded Reload
	ret
LBB0_63:
	bl	___stack_chk_fail
	.loh AdrpAdd	Lloh5, Lloh6
	.loh AdrpAdd	Lloh3, Lloh4
	.loh AdrpLdrGotLdr	Lloh0, Lloh1, Lloh2
	.loh AdrpAdd	Lloh7, Lloh8
	.loh AdrpLdr	Lloh9, Lloh10
	.loh AdrpAdd	Lloh11, Lloh12
	.loh AdrpAdd	Lloh16, Lloh17
	.loh AdrpLdrGotLdr	Lloh13, Lloh14, Lloh15
	.loh AdrpLdr	Lloh20, Lloh21
	.loh AdrpAdrp	Lloh18, Lloh20
	.loh AdrpLdr	Lloh18, Lloh19
	.loh AdrpAdd	Lloh22, Lloh23
	.loh AdrpAdd	Lloh36, Lloh37
	.loh AdrpAdd	Lloh34, Lloh35
	.loh AdrpAdd	Lloh32, Lloh33
	.loh AdrpAdd	Lloh30, Lloh31
	.loh AdrpAdd	Lloh28, Lloh29
	.loh AdrpAdd	Lloh26, Lloh27
	.loh AdrpAdd	Lloh24, Lloh25
	.loh AdrpAdd	Lloh44, Lloh45
	.loh AdrpAdd	Lloh42, Lloh43
	.loh AdrpAdd	Lloh40, Lloh41
	.loh AdrpAdd	Lloh38, Lloh39
	.loh AdrpAdd	Lloh48, Lloh49
	.loh AdrpLdr	Lloh46, Lloh47
	.loh AdrpLdrGotLdr	Lloh50, Lloh51, Lloh52
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function ijk
_ijk:                                   ; @ijk
	.cfi_startproc
; %bb.0:
	stp	x22, x21, [sp, #-32]!           ; 16-byte Folded Spill
	stp	x20, x19, [sp, #16]             ; 16-byte Folded Spill
	.cfi_def_cfa_offset 32
	.cfi_offset w19, -8
	.cfi_offset w20, -16
	.cfi_offset w21, -24
	.cfi_offset w22, -32
	cmp	w3, #1
	b.lt	LBB1_26
; %bb.1:
	cmp	w5, #1
	b.lt	LBB1_26
; %bb.2:
	mov	w9, w5
	cmp	w4, #0
	b.le	LBB1_11
; %bb.3:
	mov	w10, w4
	mov	w8, w3
	cmp	w4, #3
	b.hi	LBB1_12
; %bb.4:
	mov	x11, #0                         ; =0x0
	lsl	x12, x9, #3
	lsl	x13, x9, #2
	movi	d0, #0000000000000000
	b	LBB1_6
LBB1_5:                                 ;   in Loop: Header=BB1_6 Depth=1
	add	x11, x11, #1
	add	x2, x2, x13
	cmp	x11, x8
	b.eq	LBB1_26
LBB1_6:                                 ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_8 Depth 2
	mul	x14, x11, x10
	add	x14, x0, x14, lsl #2
	ldr	s1, [x14]
	mov	x15, x1
	mov	x16, x2
	mov	x17, x9
	b	LBB1_8
LBB1_7:                                 ;   in Loop: Header=BB1_8 Depth=2
	str	s2, [x16], #4
	add	x15, x15, #4
	subs	x17, x17, #1
	b.eq	LBB1_5
LBB1_8:                                 ;   Parent Loop BB1_6 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	s2, [x15]
	fmul	s2, s1, s2
	fadd	s2, s2, s0
	cmp	w4, #1
	b.eq	LBB1_7
; %bb.9:                                ;   in Loop: Header=BB1_8 Depth=2
	ldr	s3, [x14, #4]
	ldr	s4, [x15, x13]
	fmul	s3, s3, s4
	fadd	s2, s2, s3
	cmp	w4, #2
	b.eq	LBB1_7
; %bb.10:                               ;   in Loop: Header=BB1_8 Depth=2
	ldr	s3, [x14, #8]
	ldr	s4, [x15, x12]
	fmul	s3, s3, s4
	fadd	s2, s2, s3
	b	LBB1_7
LBB1_11:
	umull	x8, w9, w3
	lsl	x1, x8, #2
	mov	x0, x2
	ldp	x20, x19, [sp, #16]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp], #32             ; 16-byte Folded Reload
	b	_bzero
LBB1_12:
	cmp	w5, #1
	b.ne	LBB1_20
; %bb.13:
	and	x11, x10, #0x7ffffffc
	cmp	w4, #16
	b.hs	LBB1_27
; %bb.14:
	ldr	q0, [x1]
	subs	x12, x10, x11
	b.ne	LBB1_39
; %bb.15:
	lsl	x9, x9, #2
	add	x12, x0, #32
	lsl	x10, x10, #2
	movi	d1, #0000000000000000
	b	LBB1_17
LBB1_16:                                ;   in Loop: Header=BB1_17 Depth=1
	str	s2, [x2]
	add	x2, x2, x9
	add	x12, x12, x10
	subs	x8, x8, #1
	b.eq	LBB1_26
LBB1_17:                                ; =>This Inner Loop Header: Depth=1
	ldur	q2, [x12, #-32]
	fmul.4s	v2, v2, v0
	mov	s3, v2[3]
	mov	s4, v2[2]
	mov	s5, v2[1]
	fadd	s2, s2, s1
	fadd	s2, s2, s5
	fadd	s2, s2, s4
	fadd	s2, s2, s3
	cmp	x11, #4
	b.eq	LBB1_16
; %bb.18:                               ;   in Loop: Header=BB1_17 Depth=1
	ldur	q3, [x12, #-16]
	ldr	q4, [x1, #16]
	fmul.4s	v3, v3, v4
	mov	s4, v3[3]
	mov	s5, v3[2]
	mov	s6, v3[1]
	fadd	s2, s2, s3
	fadd	s2, s2, s6
	fadd	s2, s2, s5
	fadd	s2, s2, s4
	cmp	x11, #8
	b.eq	LBB1_16
; %bb.19:                               ;   in Loop: Header=BB1_17 Depth=1
	ldr	q3, [x12]
	ldr	q4, [x1, #32]
	fmul.4s	v3, v3, v4
	mov	s4, v3[3]
	mov	s5, v3[2]
	mov	s6, v3[1]
	fadd	s2, s2, s3
	fadd	s2, s2, s6
	fadd	s2, s2, s5
	fadd	s2, s2, s4
	b	LBB1_16
LBB1_20:
	mov	x11, #0                         ; =0x0
	lsl	x12, x10, #2
	lsl	x13, x9, #2
LBB1_21:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_22 Depth 2
                                        ;       Child Loop BB1_23 Depth 3
	mov	x14, #0                         ; =0x0
	mul	x15, x11, x9
	add	x15, x2, x15, lsl #2
	mov	x16, x1
LBB1_22:                                ;   Parent Loop BB1_21 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB1_23 Depth 3
	movi	d0, #0000000000000000
	mov	x17, x10
	mov	x3, x16
	mov	x4, x0
LBB1_23:                                ;   Parent Loop BB1_21 Depth=1
                                        ;     Parent Loop BB1_22 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	s1, [x4], #4
	ldr	s2, [x3]
	fmul	s1, s1, s2
	fadd	s0, s0, s1
	add	x3, x3, x13
	subs	x17, x17, #1
	b.ne	LBB1_23
; %bb.24:                               ;   in Loop: Header=BB1_22 Depth=2
	str	s0, [x15, x14, lsl #2]
	add	x14, x14, #1
	add	x16, x16, #4
	cmp	x14, x9
	b.ne	LBB1_22
; %bb.25:                               ;   in Loop: Header=BB1_21 Depth=1
	add	x11, x11, #1
	add	x0, x0, x12
	cmp	x11, x8
	b.ne	LBB1_21
LBB1_26:
	ldp	x20, x19, [sp, #16]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp], #32             ; 16-byte Folded Reload
	ret
LBB1_27:
	mov	x12, #0                         ; =0x0
	and	x13, x10, #0x7ffffff0
	and	x14, x10, #0xc
	add	x15, x0, #32
	lsl	x16, x10, #2
	add	x17, x1, #32
	sub	x3, x11, x13
	ubfx	x4, x10, #4, #27
	lsl	x5, x4, #6
	add	x4, x1, x5
	add	x5, x0, x5
	lsl	x6, x9, #2
	b	LBB1_29
LBB1_28:                                ;   in Loop: Header=BB1_29 Depth=1
	str	s0, [x2, x7, lsl #2]
	add	x12, x12, #1
	add	x15, x15, x16
	add	x5, x5, x16
	add	x0, x0, x16
	cmp	x12, x8
	b.eq	LBB1_26
LBB1_29:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_30 Depth 2
                                        ;     Child Loop BB1_34 Depth 2
                                        ;     Child Loop BB1_38 Depth 2
	mul	x7, x12, x9
	movi	d0, #0000000000000000
	mov	x19, x17
	mov	x20, x15
	mov	x21, x13
LBB1_30:                                ;   Parent Loop BB1_29 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldp	q1, q2, [x20, #-32]
	ldp	q3, q4, [x20], #64
	ldp	q5, q6, [x19, #-32]
	ldp	q7, q16, [x19], #64
	fmul.4s	v1, v1, v5
	mov	s5, v1[3]
	mov	s17, v1[2]
	mov	s18, v1[1]
	fmul.4s	v2, v2, v6
	mov	s6, v2[3]
	mov	s19, v2[2]
	mov	s20, v2[1]
	fmul.4s	v3, v3, v7
	mov	s7, v3[3]
	mov	s21, v3[2]
	mov	s22, v3[1]
	fmul.4s	v4, v4, v16
	mov	s16, v4[3]
	mov	s23, v4[2]
	mov	s24, v4[1]
	fadd	s0, s0, s1
	fadd	s0, s0, s18
	fadd	s0, s0, s17
	fadd	s0, s0, s5
	fadd	s0, s0, s2
	fadd	s0, s0, s20
	fadd	s0, s0, s19
	fadd	s0, s0, s6
	fadd	s0, s0, s3
	fadd	s0, s0, s22
	fadd	s0, s0, s21
	fadd	s0, s0, s7
	fadd	s0, s0, s4
	fadd	s0, s0, s24
	fadd	s0, s0, s23
	fadd	s0, s0, s16
	subs	x21, x21, #16
	b.ne	LBB1_30
; %bb.31:                               ;   in Loop: Header=BB1_29 Depth=1
	cmp	x13, x10
	b.eq	LBB1_28
; %bb.32:                               ;   in Loop: Header=BB1_29 Depth=1
	cbz	x14, LBB1_36
; %bb.33:                               ;   in Loop: Header=BB1_29 Depth=1
	mov	x19, x5
	mov	x20, x4
	mov	x21, x3
LBB1_34:                                ;   Parent Loop BB1_29 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	q1, [x19], #16
	ldr	q2, [x20], #16
	fmul.4s	v1, v1, v2
	mov	s2, v1[3]
	mov	s3, v1[2]
	mov	s4, v1[1]
	fadd	s0, s0, s1
	fadd	s0, s0, s4
	fadd	s0, s0, s3
	fadd	s0, s0, s2
	subs	x21, x21, #4
	b.ne	LBB1_34
; %bb.35:                               ;   in Loop: Header=BB1_29 Depth=1
	mov	x21, x11
	cmp	x10, x11
	b.eq	LBB1_28
	b	LBB1_37
LBB1_36:                                ;   in Loop: Header=BB1_29 Depth=1
	mov	x21, x13
LBB1_37:                                ;   in Loop: Header=BB1_29 Depth=1
	sub	x19, x10, x21
	madd	x20, x6, x21, x1
	add	x21, x0, x21, lsl #2
LBB1_38:                                ;   Parent Loop BB1_29 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	s1, [x21], #4
	ldr	s2, [x20]
	fmul	s1, s1, s2
	fadd	s0, s0, s1
	add	x20, x20, x6
	subs	x19, x19, #1
	b.ne	LBB1_38
	b	LBB1_28
LBB1_39:
	mov	x13, #0                         ; =0x0
	ubfx	x16, x10, #2, #29
	umull	x14, w9, w16
	add	x14, x1, x14, lsl #4
	lsl	x15, x9, #2
	add	x16, x0, x16, lsl #4
	lsl	x17, x10, #2
	movi	d1, #0000000000000000
LBB1_40:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB1_44 Depth 2
	mul	x3, x13, x10
	add	x3, x0, x3, lsl #2
	ldr	q2, [x3]
	fmul.4s	v2, v2, v0
	mov	s3, v2[3]
	mov	s4, v2[2]
	mov	s5, v2[1]
	fadd	s2, s2, s1
	fadd	s2, s2, s5
	fadd	s2, s2, s4
	fadd	s2, s2, s3
	cmp	x11, #4
	b.eq	LBB1_43
; %bb.41:                               ;   in Loop: Header=BB1_40 Depth=1
	ldr	q3, [x3, #16]
	ldr	q4, [x1, #16]
	fmul.4s	v3, v3, v4
	mov	s4, v3[3]
	mov	s5, v3[2]
	mov	s6, v3[1]
	fadd	s2, s2, s3
	fadd	s2, s2, s6
	fadd	s2, s2, s5
	fadd	s2, s2, s4
	cmp	x11, #8
	b.eq	LBB1_43
; %bb.42:                               ;   in Loop: Header=BB1_40 Depth=1
	ldr	q3, [x3, #32]
	ldr	q4, [x1, #32]
	fmul.4s	v3, v3, v4
	mov	s4, v3[3]
	mov	s5, v3[2]
	mov	s6, v3[1]
	fadd	s2, s2, s3
	fadd	s2, s2, s6
	fadd	s2, s2, s5
	fadd	s2, s2, s4
LBB1_43:                                ;   in Loop: Header=BB1_40 Depth=1
	mul	x3, x13, x9
	mov	x4, x16
	mov	x5, x14
	mov	x6, x12
LBB1_44:                                ;   Parent Loop BB1_40 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	s3, [x4], #4
	ldr	s4, [x5]
	fmul	s3, s3, s4
	fadd	s2, s2, s3
	add	x5, x5, x15
	subs	x6, x6, #1
	b.ne	LBB1_44
; %bb.45:                               ;   in Loop: Header=BB1_40 Depth=1
	str	s2, [x2, x3, lsl #2]
	add	x13, x13, #1
	add	x16, x16, x17
	cmp	x13, x8
	b.ne	LBB1_40
	b	LBB1_26
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function ikj
_ikj:                                   ; @ikj
	.cfi_startproc
; %bb.0:
	stp	x24, x23, [sp, #-64]!           ; 16-byte Folded Spill
	stp	x22, x21, [sp, #16]             ; 16-byte Folded Spill
	stp	x20, x19, [sp, #32]             ; 16-byte Folded Spill
	stp	x29, x30, [sp, #48]             ; 16-byte Folded Spill
	add	x29, sp, #48
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	mov	x19, x5
	mov	x24, x4
	mov	x23, x3
	mov	x20, x2
	mov	x22, x1
	mov	x21, x0
	smull	x8, w3, w5
	lsl	x1, x8, #2
	mov	x0, x2
	bl	_bzero
	cmp	w23, #1
	b.lt	LBB2_25
; %bb.1:
	cmp	w24, #1
	b.lt	LBB2_25
; %bb.2:
	cmp	w19, #1
	b.lt	LBB2_25
; %bb.3:
	mov	w8, w19
	mov	w9, w24
	mov	w10, w23
	cmp	w19, #4
	b.hs	LBB2_11
; %bb.4:
	mov	x11, #0                         ; =0x0
	add	x12, x22, #8
	lsl	x13, x8, #2
	lsl	x14, x9, #2
	b	LBB2_6
LBB2_5:                                 ;   in Loop: Header=BB2_6 Depth=1
	str	s0, [x15]
	add	x11, x11, #1
	add	x21, x21, x14
	cmp	x11, x10
	b.eq	LBB2_25
LBB2_6:                                 ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB2_8 Depth 2
	mul	x15, x11, x8
	add	x15, x20, x15, lsl #2
	ldr	s0, [x15]
	mov	x16, x21
	mov	x17, x12
	mov	x0, x9
	b	LBB2_8
LBB2_7:                                 ;   in Loop: Header=BB2_8 Depth=2
	ldur	s2, [x17, #-8]
	fmul	s1, s1, s2
	fadd	s0, s0, s1
	add	x17, x17, x13
	add	x16, x16, #4
	subs	x0, x0, #1
	b.eq	LBB2_5
LBB2_8:                                 ;   Parent Loop BB2_6 Depth=1
                                        ; =>  This Inner Loop Header: Depth=2
	ldr	s1, [x16]
	cmp	w19, #1
	b.eq	LBB2_7
; %bb.9:                                ;   in Loop: Header=BB2_8 Depth=2
	ldur	s2, [x17, #-4]
	fmul	s2, s1, s2
	ldr	s3, [x15, #4]
	fadd	s2, s3, s2
	str	s2, [x15, #4]
	cmp	w19, #2
	b.eq	LBB2_7
; %bb.10:                               ;   in Loop: Header=BB2_8 Depth=2
	ldr	s2, [x17]
	fmul	s2, s1, s2
	ldr	s3, [x15, #8]
	fadd	s2, s3, s2
	str	s2, [x15, #8]
	b	LBB2_7
LBB2_11:
	mov	x11, #0                         ; =0x0
	and	x12, x8, #0x7ffffff0
	and	x13, x8, #0xc
	and	x14, x8, #0x7ffffffc
	add	x15, x20, #32
	lsl	x16, x8, #2
	add	x17, x22, #32
	neg	x0, x14
	b	LBB2_13
LBB2_12:                                ;   in Loop: Header=BB2_13 Depth=1
	add	x11, x11, #1
	add	x15, x15, x16
	add	x20, x20, x16
	cmp	x11, x10
	b.eq	LBB2_25
LBB2_13:                                ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB2_15 Depth 2
                                        ;       Child Loop BB2_18 Depth 3
                                        ;       Child Loop BB2_22 Depth 3
                                        ;       Child Loop BB2_24 Depth 3
	mov	x1, #0                          ; =0x0
	mul	x2, x11, x9
	add	x2, x21, x2, lsl #2
	mov	x3, x22
	mov	x4, x17
	b	LBB2_15
LBB2_14:                                ;   in Loop: Header=BB2_15 Depth=2
	add	x1, x1, #1
	add	x4, x4, x16
	add	x3, x3, x16
	cmp	x1, x9
	b.eq	LBB2_12
LBB2_15:                                ;   Parent Loop BB2_13 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB2_18 Depth 3
                                        ;       Child Loop BB2_22 Depth 3
                                        ;       Child Loop BB2_24 Depth 3
	ldr	s0, [x2, x1, lsl #2]
	cmp	w19, #16
	b.hs	LBB2_17
; %bb.16:                               ;   in Loop: Header=BB2_15 Depth=2
	mov	x7, #0                          ; =0x0
	b	LBB2_21
LBB2_17:                                ;   in Loop: Header=BB2_15 Depth=2
	mov	x5, x4
	mov	x6, x15
	mov	x7, x12
LBB2_18:                                ;   Parent Loop BB2_13 Depth=1
                                        ;     Parent Loop BB2_15 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldp	q1, q2, [x5, #-32]
	ldp	q3, q4, [x5], #64
	fmul.4s	v1, v1, v0[0]
	fmul.4s	v2, v2, v0[0]
	fmul.4s	v3, v3, v0[0]
	fmul.4s	v4, v4, v0[0]
	ldp	q5, q6, [x6, #-32]
	ldp	q7, q16, [x6]
	fadd.4s	v1, v5, v1
	fadd.4s	v2, v6, v2
	fadd.4s	v3, v7, v3
	fadd.4s	v4, v16, v4
	stp	q1, q2, [x6, #-32]
	stp	q3, q4, [x6], #64
	subs	x7, x7, #16
	b.ne	LBB2_18
; %bb.19:                               ;   in Loop: Header=BB2_15 Depth=2
	cmp	x12, x8
	b.eq	LBB2_14
; %bb.20:                               ;   in Loop: Header=BB2_15 Depth=2
	mov	x7, x12
	mov	x5, x12
	cbz	x13, LBB2_24
LBB2_21:                                ;   in Loop: Header=BB2_15 Depth=2
	lsl	x6, x7, #2
	add	x5, x3, x6
	add	x6, x20, x6
	add	x7, x0, x7
LBB2_22:                                ;   Parent Loop BB2_13 Depth=1
                                        ;     Parent Loop BB2_15 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	q1, [x5], #16
	fmul.4s	v1, v1, v0[0]
	ldr	q2, [x6]
	fadd.4s	v1, v2, v1
	str	q1, [x6], #16
	adds	x7, x7, #4
	b.ne	LBB2_22
; %bb.23:                               ;   in Loop: Header=BB2_15 Depth=2
	mov	x5, x14
	cmp	x14, x8
	b.eq	LBB2_14
LBB2_24:                                ;   Parent Loop BB2_13 Depth=1
                                        ;     Parent Loop BB2_15 Depth=2
                                        ; =>    This Inner Loop Header: Depth=3
	ldr	s1, [x3, x5, lsl #2]
	ldr	s2, [x20, x5, lsl #2]
	fmul	s1, s0, s1
	fadd	s1, s2, s1
	str	s1, [x20, x5, lsl #2]
	add	x5, x5, #1
	cmp	x8, x5
	b.ne	LBB2_24
	b	LBB2_14
LBB2_25:
	ldp	x29, x30, [sp, #48]             ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #32]             ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #16]             ; 16-byte Folded Reload
	ldp	x24, x23, [sp], #64             ; 16-byte Folded Reload
	ret
	.cfi_endproc
                                        ; -- End function
	.p2align	2                               ; -- Begin function blocked
_blocked:                               ; @blocked
	.cfi_startproc
; %bb.0:
	sub	sp, sp, #208
	stp	x28, x27, [sp, #112]            ; 16-byte Folded Spill
	stp	x26, x25, [sp, #128]            ; 16-byte Folded Spill
	stp	x24, x23, [sp, #144]            ; 16-byte Folded Spill
	stp	x22, x21, [sp, #160]            ; 16-byte Folded Spill
	stp	x20, x19, [sp, #176]            ; 16-byte Folded Spill
	stp	x29, x30, [sp, #192]            ; 16-byte Folded Spill
	add	x29, sp, #192
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	mov	x19, x6
	mov	x20, x5
	mov	x21, x4
	mov	x22, x3
	str	x1, [sp, #32]                   ; 8-byte Folded Spill
	mov	x25, x0
	smull	x8, w3, w5
	lsl	x1, x8, #2
	str	x2, [sp, #80]                   ; 8-byte Folded Spill
	mov	x0, x2
	bl	_bzero
	cmp	w22, #1
	b.lt	LBB3_37
; %bb.1:
	cmp	w20, #1
	b.lt	LBB3_37
; %bb.2:
	cmp	w21, #1
	b.lt	LBB3_37
; %bb.3:
	mov	x13, #0                         ; =0x0
	sxtw	x8, w20
	sxtw	x9, w19
	mov	w10, w21
	ldr	x11, [sp, #80]                  ; 8-byte Folded Reload
	add	x11, x11, #32
	str	x11, [sp, #24]                  ; 8-byte Folded Spill
	smull	x11, w8, w19
	lsl	x12, x11, #2
	sbfiz	x11, x19, #2, #32
	stp	x11, x20, [sp, #40]             ; 16-byte Folded Spill
	lsl	x14, x8, #2
	ldr	x8, [sp, #32]                   ; 8-byte Folded Reload
	add	x8, x8, #32
	str	x8, [sp, #8]                    ; 8-byte Folded Spill
	str	w22, [sp, #20]                  ; 4-byte Folded Spill
	b	LBB3_5
LBB3_4:                                 ;   in Loop: Header=BB3_5 Depth=1
	ldr	x8, [sp, #24]                   ; 8-byte Folded Reload
	add	x8, x8, x12
	str	x8, [sp, #24]                   ; 8-byte Folded Spill
	ldr	x8, [sp, #80]                   ; 8-byte Folded Reload
	add	x8, x8, x12
	str	x8, [sp, #80]                   ; 8-byte Folded Spill
	ldur	x13, [x29, #-88]                ; 8-byte Folded Reload
	add	x13, x13, x9
	ldr	w22, [sp, #20]                  ; 4-byte Folded Reload
	cmp	w13, w22
	b.ge	LBB3_37
LBB3_5:                                 ; =>This Loop Header: Depth=1
                                        ;     Child Loop BB3_8 Depth 2
                                        ;       Child Loop BB3_21 Depth 3
                                        ;         Child Loop BB3_24 Depth 4
                                        ;           Child Loop BB3_26 Depth 5
                                        ;             Child Loop BB3_29 Depth 6
                                        ;             Child Loop BB3_33 Depth 6
                                        ;             Child Loop BB3_36 Depth 6
                                        ;       Child Loop BB3_12 Depth 3
                                        ;         Child Loop BB3_14 Depth 4
                                        ;           Child Loop BB3_15 Depth 5
                                        ;             Child Loop BB3_16 Depth 6
	add	w8, w13, w19
	cmp	w8, w22
	csel	w11, w8, w22, lt
	stur	x13, [x29, #-88]                ; 8-byte Folded Spill
	cmp	w11, w13
	b.le	LBB3_4
; %bb.6:                                ;   in Loop: Header=BB3_5 Depth=1
	mov	x8, #0                          ; =0x0
	mov	x16, #0                         ; =0x0
	sxtw	x17, w11
	ldr	x11, [sp, #32]                  ; 8-byte Folded Reload
	str	x11, [sp, #64]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #80]                  ; 8-byte Folded Reload
	str	x11, [sp, #96]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #8]                   ; 8-byte Folded Reload
	str	x11, [sp, #56]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #24]                  ; 8-byte Folded Reload
	str	x11, [sp, #88]                  ; 8-byte Folded Spill
	b	LBB3_8
LBB3_7:                                 ;   in Loop: Header=BB3_8 Depth=2
	ldp	x8, x20, [sp, #40]              ; 16-byte Folded Reload
	ldr	x11, [sp, #88]                  ; 8-byte Folded Reload
	add	x11, x11, x8
	str	x11, [sp, #88]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #56]                  ; 8-byte Folded Reload
	add	x11, x11, x8
	str	x11, [sp, #56]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #96]                  ; 8-byte Folded Reload
	add	x11, x11, x8
	str	x11, [sp, #96]                  ; 8-byte Folded Spill
	ldr	x11, [sp, #64]                  ; 8-byte Folded Reload
	add	x11, x11, x8
	str	x11, [sp, #64]                  ; 8-byte Folded Spill
	add	x16, x16, x9
	cmp	w16, w20
	ldr	x8, [sp, #72]                   ; 8-byte Folded Reload
	b.ge	LBB3_4
LBB3_8:                                 ;   Parent Loop BB3_5 Depth=1
                                        ; =>  This Loop Header: Depth=2
                                        ;       Child Loop BB3_21 Depth 3
                                        ;         Child Loop BB3_24 Depth 4
                                        ;           Child Loop BB3_26 Depth 5
                                        ;             Child Loop BB3_29 Depth 6
                                        ;             Child Loop BB3_33 Depth 6
                                        ;             Child Loop BB3_36 Depth 6
                                        ;       Child Loop BB3_12 Depth 3
                                        ;         Child Loop BB3_14 Depth 4
                                        ;           Child Loop BB3_15 Depth 5
                                        ;             Child Loop BB3_16 Depth 6
	add	x11, x8, #1
	str	x11, [sp, #72]                  ; 8-byte Folded Spill
	add	w11, w16, w19
	cmp	w11, w20
	csel	w11, w11, w20, lt
	cmp	w11, w16
	b.le	LBB3_7
; %bb.9:                                ;   in Loop: Header=BB3_8 Depth=2
	ldr	x13, [sp, #72]                  ; 8-byte Folded Reload
	mul	w13, w13, w19
	ldr	x15, [sp, #48]                  ; 8-byte Folded Reload
	cmp	w15, w13
	csel	w13, w15, w13, lt
	sxtw	x13, w13
	add	x15, x16, #1
	cmp	x13, x15
	csinc	x13, x13, x16, gt
	msub	x6, x8, x9, x13
	sxtw	x5, w11
	cmp	x6, #4
	b.hs	LBB3_19
; %bb.10:                               ;   in Loop: Header=BB3_8 Depth=2
	mov	x8, #0                          ; =0x0
	ldr	x13, [sp, #64]                  ; 8-byte Folded Reload
	b	LBB3_12
LBB3_11:                                ;   in Loop: Header=BB3_12 Depth=3
	add	x13, x13, x12
	add	x8, x8, x9
	cmp	w8, w21
	b.ge	LBB3_7
LBB3_12:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ; =>    This Loop Header: Depth=3
                                        ;         Child Loop BB3_14 Depth 4
                                        ;           Child Loop BB3_15 Depth 5
                                        ;             Child Loop BB3_16 Depth 6
	add	w11, w8, w19
	cmp	w11, w21
	csel	w11, w11, w21, lt
	cmp	w11, w8
	b.le	LBB3_11
; %bb.13:                               ;   in Loop: Header=BB3_12 Depth=3
	sxtw	x15, w11
	ldr	x0, [sp, #96]                   ; 8-byte Folded Reload
	ldur	x2, [x29, #-88]                 ; 8-byte Folded Reload
LBB3_14:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_12 Depth=3
                                        ; =>      This Loop Header: Depth=4
                                        ;           Child Loop BB3_15 Depth 5
                                        ;             Child Loop BB3_16 Depth 6
	mul	x11, x2, x10
	add	x11, x25, x11, lsl #2
	mov	x1, x13
	mov	x3, x8
LBB3_15:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_12 Depth=3
                                        ;         Parent Loop BB3_14 Depth=4
                                        ; =>        This Loop Header: Depth=5
                                        ;             Child Loop BB3_16 Depth 6
	mov	x4, #0                          ; =0x0
	ldr	s0, [x11, x3, lsl #2]
LBB3_16:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_12 Depth=3
                                        ;         Parent Loop BB3_14 Depth=4
                                        ;           Parent Loop BB3_15 Depth=5
                                        ; =>          This Inner Loop Header: Depth=6
	ldr	s1, [x1, x4, lsl #2]
	fmul	s1, s0, s1
	ldr	s2, [x0, x4, lsl #2]
	fadd	s1, s2, s1
	str	s1, [x0, x4, lsl #2]
	add	x4, x4, #1
	add	x6, x16, x4
	cmp	x6, x5
	b.lt	LBB3_16
; %bb.17:                               ;   in Loop: Header=BB3_15 Depth=5
	add	x3, x3, #1
	add	x1, x1, x14
	cmp	x3, x15
	b.lt	LBB3_15
; %bb.18:                               ;   in Loop: Header=BB3_14 Depth=4
	add	x2, x2, #1
	add	x0, x0, x14
	cmp	x2, x17
	b.lt	LBB3_14
	b	LBB3_11
LBB3_19:                                ;   in Loop: Header=BB3_8 Depth=2
	mov	x0, #0                          ; =0x0
	and	x1, x6, #0xfffffffffffffff0
	and	x27, x6, #0xc
	and	x28, x6, #0xfffffffffffffffc
	neg	x30, x28
	ldr	x20, [sp, #32]                  ; 8-byte Folded Reload
	ldr	x4, [sp, #56]                   ; 8-byte Folded Reload
	b	LBB3_21
LBB3_20:                                ;   in Loop: Header=BB3_21 Depth=3
	add	x4, x4, x12
	add	x20, x20, x12
	add	x0, x0, x9
	cmp	w0, w21
	b.ge	LBB3_7
LBB3_21:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ; =>    This Loop Header: Depth=3
                                        ;         Child Loop BB3_24 Depth 4
                                        ;           Child Loop BB3_26 Depth 5
                                        ;             Child Loop BB3_29 Depth 6
                                        ;             Child Loop BB3_33 Depth 6
                                        ;             Child Loop BB3_36 Depth 6
	add	w8, w0, w19
	cmp	w8, w21
	csel	w8, w8, w21, lt
	cmp	w8, w0
	b.le	LBB3_20
; %bb.22:                               ;   in Loop: Header=BB3_21 Depth=3
	sxtw	x22, w8
	ldp	x23, x11, [sp, #80]             ; 16-byte Folded Reload
	ldur	x8, [x29, #-88]                 ; 8-byte Folded Reload
	b	LBB3_24
LBB3_23:                                ;   in Loop: Header=BB3_24 Depth=4
	add	x8, x8, #1
	add	x11, x11, x14
	add	x23, x23, x14
	cmp	x8, x17
	b.ge	LBB3_20
LBB3_24:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_21 Depth=3
                                        ; =>      This Loop Header: Depth=4
                                        ;           Child Loop BB3_26 Depth 5
                                        ;             Child Loop BB3_29 Depth 6
                                        ;             Child Loop BB3_33 Depth 6
                                        ;             Child Loop BB3_36 Depth 6
	mul	x13, x8, x10
	add	x13, x25, x13, lsl #2
	mov	x24, x20
	mov	x15, x4
	mov	x7, x0
	b	LBB3_26
LBB3_25:                                ;   in Loop: Header=BB3_26 Depth=5
	add	x7, x7, #1
	add	x15, x15, x14
	add	x24, x24, x14
	cmp	x7, x22
	b.ge	LBB3_23
LBB3_26:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_21 Depth=3
                                        ;         Parent Loop BB3_24 Depth=4
                                        ; =>        This Loop Header: Depth=5
                                        ;             Child Loop BB3_29 Depth 6
                                        ;             Child Loop BB3_33 Depth 6
                                        ;             Child Loop BB3_36 Depth 6
	ldr	s0, [x13, x7, lsl #2]
	cmp	x6, #16
	b.hs	LBB3_28
; %bb.27:                               ;   in Loop: Header=BB3_26 Depth=5
	mov	x3, #0                          ; =0x0
	b	LBB3_32
LBB3_28:                                ;   in Loop: Header=BB3_26 Depth=5
	mov	x2, x15
	mov	x3, x11
	mov	x26, x1
LBB3_29:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_21 Depth=3
                                        ;         Parent Loop BB3_24 Depth=4
                                        ;           Parent Loop BB3_26 Depth=5
                                        ; =>          This Inner Loop Header: Depth=6
	ldp	q1, q2, [x2, #-32]
	ldp	q3, q4, [x2], #64
	fmul.4s	v1, v1, v0[0]
	fmul.4s	v2, v2, v0[0]
	fmul.4s	v3, v3, v0[0]
	fmul.4s	v4, v4, v0[0]
	ldp	q5, q6, [x3, #-32]
	ldp	q7, q16, [x3]
	fadd.4s	v1, v5, v1
	fadd.4s	v2, v6, v2
	fadd.4s	v3, v7, v3
	fadd.4s	v4, v16, v4
	stp	q1, q2, [x3, #-32]
	stp	q3, q4, [x3], #64
	subs	x26, x26, #16
	b.ne	LBB3_29
; %bb.30:                               ;   in Loop: Header=BB3_26 Depth=5
	cmp	x6, x1
	b.eq	LBB3_25
; %bb.31:                               ;   in Loop: Header=BB3_26 Depth=5
	mov	x3, x1
	mov	x2, x1
	cbz	x27, LBB3_35
LBB3_32:                                ;   in Loop: Header=BB3_26 Depth=5
	add	x2, x30, x3
	add	x3, x16, x3
	lsl	x26, x3, #2
	add	x3, x24, x26
	add	x26, x23, x26
LBB3_33:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_21 Depth=3
                                        ;         Parent Loop BB3_24 Depth=4
                                        ;           Parent Loop BB3_26 Depth=5
                                        ; =>          This Inner Loop Header: Depth=6
	ldr	q1, [x3], #16
	fmul.4s	v1, v1, v0[0]
	ldr	q2, [x26]
	fadd.4s	v1, v2, v1
	str	q1, [x26], #16
	adds	x2, x2, #4
	b.ne	LBB3_33
; %bb.34:                               ;   in Loop: Header=BB3_26 Depth=5
	mov	x2, x28
	cmp	x6, x28
	b.eq	LBB3_25
LBB3_35:                                ;   in Loop: Header=BB3_26 Depth=5
	add	x2, x16, x2
LBB3_36:                                ;   Parent Loop BB3_5 Depth=1
                                        ;     Parent Loop BB3_8 Depth=2
                                        ;       Parent Loop BB3_21 Depth=3
                                        ;         Parent Loop BB3_24 Depth=4
                                        ;           Parent Loop BB3_26 Depth=5
                                        ; =>          This Inner Loop Header: Depth=6
	ldr	s1, [x24, x2, lsl #2]
	ldr	s2, [x23, x2, lsl #2]
	fmul	s1, s0, s1
	fadd	s1, s2, s1
	str	s1, [x23, x2, lsl #2]
	add	x2, x2, #1
	cmp	x2, x5
	b.lt	LBB3_36
	b	LBB3_25
LBB3_37:
	ldp	x29, x30, [sp, #192]            ; 16-byte Folded Reload
	ldp	x20, x19, [sp, #176]            ; 16-byte Folded Reload
	ldp	x22, x21, [sp, #160]            ; 16-byte Folded Reload
	ldp	x24, x23, [sp, #144]            ; 16-byte Folded Reload
	ldp	x26, x25, [sp, #128]            ; 16-byte Folded Reload
	ldp	x28, x27, [sp, #112]            ; 16-byte Folded Reload
	add	sp, sp, #208
	ret
	.cfi_endproc
                                        ; -- End function
	.section	__TEXT,__const
	.p2align	2, 0x0                          ; @__const.main.shapes
l___const.main.shapes:
	.long	64                              ; 0x40
	.long	64                              ; 0x40
	.long	64                              ; 0x40
	.long	128                             ; 0x80
	.long	512                             ; 0x200
	.long	64                              ; 0x40
	.long	256                             ; 0x100
	.long	128                             ; 0x80
	.long	256                             ; 0x100
	.long	127                             ; 0x7f
	.long	257                             ; 0x101
	.long	65                              ; 0x41

	.section	__TEXT,__cstring,cstring_literals
l_.str:                                 ; @.str
	.asciz	"ijk"

l_.str.1:                               ; @.str.1
	.asciz	"ikj"

l_.str.2:                               ; @.str.2
	.asciz	"blocked"

	.section	__DATA,__const
	.p2align	3, 0x0                          ; @__const.main.methods
l___const.main.methods:
	.quad	l_.str
	.quad	_ijk
	.long	0                               ; 0x0
	.space	4
	.quad	l_.str.1
	.quad	_ikj
	.long	0                               ; 0x0
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	8                               ; 0x8
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	16                              ; 0x10
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	32                              ; 0x20
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	64                              ; 0x40
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	128                             ; 0x80
	.space	4
	.quad	l_.str.2
	.quad	_blocked
	.long	256                             ; 0x100
	.space	4

	.section	__TEXT,__cstring,cstring_literals
l_.str.3:                               ; @.str.3
	.asciz	"{\"trials\":%d,\"seed\":501,\"rows\":[\n"

l_.str.4:                               ; @.str.4
	.asciz	"validation failure shape=%d candidate=%d index=%d\n"

.zerofill __DATA,__bss,_sink,8,3        ; @sink
l_.str.5:                               ; @.str.5
	.asciz	"%s{\"m\":%d,\"k\":%d,\"n\":%d,\"method\":\"%s\",\"tile\":%d,\"repeats\":%d,\"max_abs_error\":%.9g,\"samples_us\":["

l_.str.6:                               ; @.str.6
	.space	1

l_.str.7:                               ; @.str.7
	.asciz	",\n"

l_.str.8:                               ; @.str.8
	.asciz	"%s%.9g"

l_.str.9:                               ; @.str.9
	.asciz	","

l_.str.10:                              ; @.str.10
	.asciz	"]}"

l_.str.11:                              ; @.str.11
	.asciz	"\n],\"checksum\":%.9g}\n"

	.section	__DATA,__data
	.p2align	2, 0x0                          ; @state
_state:
	.long	501                             ; 0x1f5

.subsections_via_symbols
