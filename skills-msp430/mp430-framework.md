---
name: msp430-framework
description: TI MSP430FR5994 LaunchPad + msp430-gcc skill for 1 Hz onboard LED blink with GPIO3 reserved for LCD-side usage.
---

# TI MSP430FR5994 LaunchPad + msp430-gcc Skill: 1 Hz LED Blink with GPIO3 LCD Reservation

## 1) Task requirement analysis

Target task:

> Blink the onboard LED at 1 Hz.  
> Use GPIO 3 for the LCD.

### Requirement decomposition
- **Main behavior**: onboard LED must blink at exactly **1 Hz**.
- **Timing interpretation**:
  - 1 full cycle = 1000 ms.
  - Typical blink waveform: 500 ms ON + 500 ms OFF.
- **Pin ownership**:
  - GPIO3 is allocated to LCD-related signaling/wiring.
  - LED control pin should be independent from GPIO3 unless schematic explicitly multiplexes it.

### Domain knowledge needed
- MSP430 GPIO register control (`PxDIR`, `PxOUT`, optional `PxREN`, `PxSEL0/1` depending device family).
- MSP430FR5994 LaunchPad pin map specifics (onboard LED pins and header mapping).
- Delay generation using `__delay_cycles()` with known `F_CPU`/DCO clock.
- Build/flash toolchain basics for `msp430-gcc` (`cl430`, linker scripts/startup files, programmer tools).
- LCD pin reservation strategy for incremental integration.

### Risks to validate before coding
- “GPIO 3” naming ambiguity (port + bit required, e.g., `P1.3` vs generic “digital pin 3”).
- Onboard LED pin differs by board model; for MSP430FR5994 LaunchPad, verify LED mapping from TI board docs before flashing.
- Blink frequency drift if clock config is unknown or unstable.

---

## 2) Platform guidance: MSP430FR5994 LaunchPad + msp430-gcc

### Minimal implementation flow
1. Confirm exact board: **MSP-EXP430FR5994 LaunchPad**.
2. Resolve pins from board docs/schematic:
   - `LED_PIN` (onboard LED)
   - `LCD_GPIO3_PIN` (LCD reserved signal, e.g., button/UART conflict check)
3. Set GPIO directions:
   - LED as output.
   - LCD GPIO3 as output placeholder (or required idle state).
4. Configure clock assumptions (or document default DCO assumptions).
5. Implement deterministic 500 ms toggle intervals.

### FR5994-specific note
- Keep all pin mappings in one section at the top of your source (e.g., `LED_PORT`, `LED_BIT`, `LCD_PORT`, `LCD_BIT`) and adjust only there.
- Treat `GPIO 3` as a task-level alias; convert it to an explicit FR5994 port/bit (for example `P1.3`) based on your wiring.

---

## 3) Reusable skill patterns

## Pattern A — Busy-wait with `__delay_cycles()` (simple)

```c
#include <msp430.h>

#ifndef F_CPU
#define F_CPU 1000000UL  // 1 MHz default assumption
#endif

#define LED_DIR   P1DIR
#define LED_OUT   P1OUT
#define LED_BIT   BIT0      // Replace with FR5994 onboard LED bit per your board schematic

#define LCD_DIR   P1DIR
#define LCD_OUT   P1OUT
#define LCD_BIT   BIT3      // Example mapping: "GPIO 3 for LCD" => P1.3

static void delay_ms(unsigned int ms) {
    while (ms--) {
        __delay_cycles(F_CPU / 1000UL);
    }
}

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;   // Stop watchdog

    // GPIO setup
    LED_DIR |= LED_BIT;
    LED_OUT &= ~LED_BIT;

    LCD_DIR |= LCD_BIT;
    LCD_OUT &= ~LCD_BIT;        // Idle low for reserved LCD signal

    while (1) {
        LED_OUT ^= LED_BIT;     // Toggle LED
        delay_ms(500);          // 500ms high/low halves -> 1Hz full cycle
    }
}
```

**When to use**
- Basic lab demos.
- No concurrent tasks.

## Pattern B — Timer-driven toggle (better timing stability)

```c
#include <msp430.h>

#define LED_DIR   P1DIR
#define LED_OUT   P1OUT
#define LED_BIT   BIT0      // Replace with FR5994 onboard LED bit per board docs

#define LCD_DIR   P1DIR
#define LCD_OUT   P1OUT
#define LCD_BIT   BIT3

int main(void) {
    WDTCTL = WDTPW | WDTHOLD;

    LED_DIR |= LED_BIT;
    LED_OUT &= ~LED_BIT;

    LCD_DIR |= LCD_BIT;
    LCD_OUT &= ~LCD_BIT;

    // Assume SMCLK ~1MHz; divide for manageable timer count
    TA0CTL = TASSEL__SMCLK | ID__8 | MC__UP | TACLR; // /8 -> 125kHz
    TA0CCR0 = 62500 - 1;  // 500ms period at 125kHz
    TA0CCTL0 = CCIE;

    __bis_SR_register(GIE); // Enable global interrupts

    while (1) {
        __bis_SR_register(LPM0_bits | GIE); // Sleep; wake on timer ISR
    }
}

#pragma vector=TIMER0_A0_VECTOR
__interrupt void Timer_A(void) {
    LED_OUT ^= LED_BIT; // toggle every 500ms => 1Hz blink cycle
}
```

**When to use**
- Better period consistency.
- Expanding to LCD updates/input handling.

---

## 4) Reusable usage template

For MSP430 GCC tasks with fixed pin constraints:

1. Define explicit pin map macros (`LED_*`, `LCD_*`, etc.).
2. Freeze clock assumption (or configure clock explicitly).
3. Choose timing model:
   - busy-wait for quick prototype,
   - timer ISR for accurate periodic behavior.
4. Reserve non-active peripheral pins at known idle states.
5. Document mapping assumptions (`GPIO3 => P1.3`) in comments.

---

## 5) Troubleshooting checklist

- **LED never toggles**:
  - wrong LED pin macro,
  - watchdog not stopped,
  - pin not configured as output.
- **Frequency not 1 Hz**:
  - wrong `F_CPU` assumption,
  - timer divider/CCR miscalculation.
- **GPIO3 conflict issues**:
  - `P1.3` overlaps button/UART or board default function,
  - missing function-select reset on FR-series devices.
- **Unexpected resets**:
  - watchdog left enabled,
  - unstable clock configuration.

---

## 6) Reuse scope

This skill generalizes to:
- heartbeat LED diagnostics on MSP430,
- pin-constrained firmware where one GPIO is pre-assigned to LCD,
- migration from blocking prototypes to timer-driven production behavior under `msp430-gcc`.
