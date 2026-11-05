/* KCD1 grass patch B: blend merged-grass spine points between two 35 ms simulation steps.
 * Runs inside WHGame.dll's spine simulator (function 0x18051f698), hooked at 0x180522f96 in the
 * per-point store loop, AFTER the simulated point and its speed were saved back and BEFORE the
 * point is converted to local space for the mesh build.
 *   in:  rbp = frame, [rbp+0x230] = 3*index of this spine's root point
 *        r10 = spine array (24-byte points: pos @0, speed @0xc; root speed.y = left-over time in ms)
 *        rsi = speeds of this frame (12-byte), r15 = positions (12-byte), rcx*4 = byte index of the point
 *   does: pos += speed * -(35 ms - leftover) / 1000     (= pose between the previous and the last step)
 *   then the two instructions the hook replaced, then jumps back to 0x180522fa0.
 *   free at the hook: rax, xmm4, xmm5 (all rewritten by the game before their next read); flags are dead.
 */
    .intel_syntax noprefix
    .text
    .globl cave_start, cave_tail, cave_end
cave_start:
    mov   rax, qword ptr [rbp+0x230]
    movss xmm4, dword ptr [rip+c35]
    subss xmm4, dword ptr [r10+rax*8+0x10]
    mulss xmm4, dword ptr [rip+cneg]
    movss xmm5, dword ptr [rsi+rcx*4]
    mulss xmm5, xmm4
    addss xmm5, dword ptr [r15+rcx*4]
    movss dword ptr [r15+rcx*4], xmm5
    movss xmm5, dword ptr [rsi+rcx*4+4]
    mulss xmm5, xmm4
    addss xmm5, dword ptr [r15+rcx*4+4]
    movss dword ptr [r15+rcx*4+4], xmm5
    movss xmm5, dword ptr [rsi+rcx*4+8]
    mulss xmm5, xmm4
    addss xmm5, dword ptr [r15+rcx*4+8]
    movss dword ptr [r15+rcx*4+8], xmm5
    add   rdx, 0x18                      /* replaced instruction 1 */
    mulss xmm6, dword ptr [r15+rcx*4]    /* replaced instruction 2 (reads the blended x) */
cave_tail:
#ifdef TEST
    ret
    .byte 0x90, 0x90, 0x90, 0x90
#else
    .byte 0xE9
    .long 0                              /* rel32 to 0x180522fa0, filled in by the patcher */
#endif
    .balign 4, 0xCC
c35:  .float 35.0
cneg: .float -0.001
cave_end:

#ifdef TEST
/* void run_cave(struct regs *r)  -- SysV wrapper for the native test */
    .globl run_cave
run_cave:
    push rbp
    push rbx
    push r15
    push r12
    mov  r12, rdi
    mov  rbp, qword ptr [r12+0]
    mov  r10, qword ptr [r12+8]
    mov  rsi, qword ptr [r12+16]
    mov  r15, qword ptr [r12+24]
    mov  rcx, qword ptr [r12+32]
    mov  rdx, qword ptr [r12+40]
    movss xmm6, dword ptr [r12+48]
    call cave_start
    mov  qword ptr [r12+40], rdx
    movss dword ptr [r12+52], xmm6
    pop  r12
    pop  r15
    pop  rbx
    pop  rbp
    ret
    .section .note.GNU-stack,"",@progbits
#endif
