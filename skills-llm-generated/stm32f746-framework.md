---
name: stm32f746-framework
description: STM32F746 + STM32CubeHAL skill for LCD random digit display (0-9) updated on GPIO2 button press, with GPIO3 mapped to LCD-side signaling when required.
---

# STM32F746 + STM32CubeHAL Skill: Random 0–9 on LCD, Change on Button Press

## 1) Task analysis

Target task:

> Randomly show a number from 0 to 9 on LCD screen, change number when button is pressed.  
> Use GPIO 3 for the LCD and GPIO 2 for the button.

### Functional requirements
- LCD must show one digit from `0` to `9`.
- A **new random digit** must be generated only on a valid button press event.
- GPIO mapping constraints:
  - `GPIO 2` is the button input.
  - `GPIO 3` is reserved for LCD-side mapping/signaling (only if the LCD wiring actually uses direct GPIO signaling).

### Required domain knowledge
- STM32CubeHAL startup flow: `HAL_Init()`, clock config, peripheral init.
- GPIO input/output configuration and pin-state reads.
- Debouncing methods (polling debounce or EXTI interrupt debounce gate).
- LCD rendering path for STM32F746:
  - TFT via BSP/LTDC (`BSP_LCD_*`) on Discovery-style boards, or
  - GPIO-driven character LCD interface if external module is used.
- Pseudo-random generation with `rand() % 10` and one-time seeding using `srand()`.

### Key risks to resolve early
- “GPIO 2/3” is incomplete without port naming (`PA2`, `PB2`, etc.).
- Button bounce causes repeated/unintended updates.
- On STM32746G-Discovery, the onboard LCD path is usually LTDC/BSP, not one direct GPIO data line.

---

## 2) Platform implementation guidance (stm32f746 + STM32CubeHAL)

1. Create or open STM32F746 CubeMX/CubeIDE project.
2. Resolve exact mapping from schematic:
   - `BUTTON_Pin = GPIO_PIN_2`, `BUTTON_GPIO_Port = GPIOx`
   - `LCD_SIGNAL_Pin = GPIO_PIN_3`, `LCD_SIGNAL_GPIO_Port = GPIOx` (only if your LCD design needs this)
3. Configure button input:
   - polling: `GPIO_MODE_INPUT`, or
   - interrupt: `GPIO_MODE_IT_FALLING` (or rising, based on wiring).
4. Configure pull-up/pull-down to match hardware.
5. Initialize LCD stack (`BSP_LCD_Init` path or external LCD driver path).
6. Seed PRNG once at startup.
7. On accepted press event: generate new value `0..9`, redraw only needed LCD region.

---

## 3) Reusable skill patterns

## Pattern A — Polling + debounce (simple)

```c
#include "main.h"
#include "stm32746g_discovery_lcd.h"
#include <stdio.h>
#include <stdlib.h>

#define BUTTON_GPIO_Port   GPIOA
#define BUTTON_Pin         GPIO_PIN_2
#define LCD_SIG_GPIO_Port  GPIOA
#define LCD_SIG_Pin        GPIO_PIN_3

static void MX_GPIO_Custom_Init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef GPIO_InitStruct = {0};

    // GPIO3 reserved for LCD-side signal if needed by hardware design
    GPIO_InitStruct.Pin = LCD_SIG_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LCD_SIG_GPIO_Port, &GPIO_InitStruct);

    // Button input on GPIO2 (example: pull-up + active low button)
    GPIO_InitStruct.Pin = BUTTON_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(BUTTON_GPIO_Port, &GPIO_InitStruct);
}

static void LCD_Init_Custom(void)
{
    BSP_LCD_Init();
    BSP_LCD_LayerDefaultInit(0, LCD_FB_START_ADDRESS);
    BSP_LCD_SelectLayer(0);
    BSP_LCD_Clear(LCD_COLOR_BLACK);
    BSP_LCD_SetBackColor(LCD_COLOR_BLACK);
    BSP_LCD_SetTextColor(LCD_COLOR_GREEN);
    BSP_LCD_SetFont(&Font24);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Custom_Init();
    LCD_Init_Custom();

    srand((unsigned int)(HAL_GetTick() ^ 0x9E3779B9u));

    GPIO_PinState last = HAL_GPIO_ReadPin(BUTTON_GPIO_Port, BUTTON_Pin);
    uint32_t last_event_ms = 0;
    const uint32_t debounce_ms = 30;

    char buf[24];

    while (1)
    {
        GPIO_PinState now = HAL_GPIO_ReadPin(BUTTON_GPIO_Port, BUTTON_Pin);

        // For pull-up wiring: valid press = HIGH -> LOW
        if (last == GPIO_PIN_SET && now == GPIO_PIN_RESET)
        {
            uint32_t t = HAL_GetTick();
            if ((t - last_event_ms) >= debounce_ms)
            {
                int value = rand() % 10;

                BSP_LCD_ClearStringLine(6);
                snprintf(buf, sizeof(buf), "RANDOM: %d", value);
                BSP_LCD_DisplayStringAt(0, LINE(6), (uint8_t *)buf, CENTER_MODE);

                // Optional GPIO3 pulse/toggle for LCD-side signaling profile
                HAL_GPIO_TogglePin(LCD_SIG_GPIO_Port, LCD_SIG_Pin);
                last_event_ms = t;
            }
        }

        last = now;
        HAL_Delay(1);
    }
}
```

---

## 4) Reusable usage template for similar tasks

Use this template for "random sensor/status rendering" tasks:

1. `Display_Init()` for target LCD/OLED driver.
2. `Random_Init(seed_source)` and define random range `[min, max]`.
3. Choose scheduler:
   - `HAL_Delay()` loop for quick demos.
   - timer interrupt + event flag for scalable firmware.
4. Use bounded formatting (`snprintf`) and fixed display line/region.
5. Add anti-flicker strategy (line-only clear, dirty-rect redraw, double-buffering when available).

---

## 5) Randomness quality options

- **Basic**: seed with `HAL_GetTick()` (easy, low entropy).
- **Better**: mix in RTC subseconds, unconnected ADC noise, unique ID registers.
- **Best (if needed)**: hardware RNG peripheral on MCU variants that provide it.

For tasks that only require visibly varying digits, `rand()%10` with non-constant seed is typically sufficient.

---

## 6) Troubleshooting checklist

- Nothing displayed:
  - wrong BSP LCD include/init sequence,
  - layer/framebuffer not initialized,
  - text color same as background.
- Number never changes:
  - `srand()` missing or fixed seed,
  - timer callback not firing.
- Heavy flicker:
  - avoid full-screen clears each update; clear one line/region only.
- Update timing wrong:
  - system clock or timer PSC/ARR mismatch.

---

## 7) Skill reuse scope

This skill generalizes to:
- random quiz/UI prompts on LCD,
- pseudo-random demo states for validation,
- periodic data rendering tasks on STM32CubeHAL display stacks.