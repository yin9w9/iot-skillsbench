---
name: msp430-framework
description: TI MSP430FR5994 LaunchPad + msp430-gcc/cl430 GPIO skill for LED1, LED2, and S2 button tasks.
---

# MSP430FR5994 LaunchPad GPIO Skill

## Requirements

Use bare-metal C with `<msp430.h>` for the TI MSP430FR5994 LaunchPad.

Task pins:

- LED1: `P1.0`
- LED2: `P1.1`
- S2 button: `P5.5`

Board note:

- LED2 is driven by `P1.1`.
- On the board, `P1.1` connects through `R101` to `LED101`.
- Firmware must control `P1.1`; do not treat `R101` or `LED101` as GPIO pins.

Important MSP430FR5994 setup:

- Stop the watchdog with `WDTCTL = WDTPW + WDTHOLD;`
- Configure GPIO direction with `PxDIR`.
- Write output pins with `PxOUT`.
- Clear high-impedance GPIO lock with `PM5CTL0 &= ~LOCKLPM5;`
- S2 uses a pull-up resistor, so pressed means the input reads `0`.

## Blink LED2 At 1 Hz

Use this for `Blink_1Hz_LED`.

```c
#include <msp430.h>

int main(void)
{
    WDTCTL = WDTPW + WDTHOLD;

    P1DIR |= BIT1;              /* P1.1 output: LED2 / LED101 */
    P1OUT &= ~BIT1;             /* LED2 off */

    PM5CTL0 &= ~LOCKLPM5;

    for (;;) {
        P1OUT ^= BIT1;          /* Toggle P1.1 */
        __delay_cycles(500000); /* 500 ms at 1 MHz: 1 Hz blink cycle */
    }
}
```

## Blink LED1 At 2 Hz

Use this for `Blink_2Hz_LED`.

```c
#include <msp430.h>

int main(void)
{
    WDTCTL = WDTPW + WDTHOLD;

    P1DIR |= BIT0;              /* P1.0 output: LED1 */
    P1OUT &= ~BIT0;             /* LED1 off */

    PM5CTL0 &= ~LOCKLPM5;

    for (;;) {
        P1OUT ^= BIT0;          /* Toggle P1.0 */
        __delay_cycles(250000); /* 250 ms at 1 MHz: 2 Hz blink cycle */
    }
}
```

Equivalent raw-mask style for LED1:

```c
P1DIR |= 0x01;
P1OUT ^= 0x01;
```

`0x01` is `BIT0`, so it controls `P1.0`. For LED2 on `P1.1`, use `BIT1` or `0x02`.

## Turn On LED1 When S2 Is Pressed

Use this for `Botton_to_LED`.

```c
#include <msp430.h>

int main(void)
{
    WDTCTL = WDTPW + WDTHOLD;

    P1DIR |= BIT0;      /* LED1 output */
    P1OUT &= ~BIT0;     /* LED1 off */

    P5DIR &= ~BIT5;     /* S2 input */
    P5REN |= BIT5;      /* Enable pull resistor */
    P5OUT |= BIT5;      /* Pull-up: released = 1, pressed = 0 */

    PM5CTL0 &= ~LOCKLPM5;

    for (;;) {
        if ((P5IN & BIT5) == 0) {
            P1OUT |= BIT0;      /* S2 pressed: LED1 on */
        } else {
            P1OUT &= ~BIT0;     /* S2 released: LED1 off */
        }
    }
}
```

## Quick Troubleshooting

- If LED works only after pressing RESET, the debugger probably left the MCU halted after flashing. Use Run/Resume, reset-and-run, or power-cycle after programming.
- If LED does not turn on, confirm `PM5CTL0 &= ~LOCKLPM5;` is present.
- If LED2 does not turn on, confirm code drives `P1.1` and the board path is `P1.1 -> R101 -> LED101`.
- If S2 does not affect LED1, confirm S2 is really connected to `P5.5` and remember it is active-low.
