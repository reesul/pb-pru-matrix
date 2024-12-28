#include "pru_led_matrix.h"


volatile register uint32_t __R30;
volatile register uint32_t __R31;

uint32_t *gpio0 = (uint32_t *)GPIO0;
uint32_t *gpio1 = (uint32_t *)GPIO1;
uint32_t *gpio2 = (uint32_t *)GPIO2;
uint32_t *gpio3 = (uint32_t *)GPIO3;


const uint32_t CLEAR_COLOR_BITS = 1 << PRU_R1 | 1 << PRU_G1 | 1  << PRU_B1 | 1 << PRU_R2 | 1 << PRU_G2 | 1 <<PRU_B2;

static inline void set_pru_bits(uint32_t data)
{
    __R30 |= data;
}

static inline void clear_pru_bits(uint32_t data)
{
    __R30 &= ~data;
}

/**
 * Will need to code this a bit more tightly for performant version. Integrate w/ other functions at least
*/
void write_color_bits(uint8_t r1, uint8_t g1, uint8_t b1, \
        uint8_t r2, uint8_t g2, uint8_t b2)
{
    uint32_t color_bits = r1 << PRU_R1 | g1 << PRU_G1 | b1  << PRU_B1 |
        r2 << PRU_R2 | g2 << PRU_G2 | b2 <<PRU_B2;

    clear_pru_bits(CLEAR_COLOR_BITS); //make sure they are all in off state by default. No state from last iteration.
    __delay_cycles(10);    
    clear_pru_bits(CLK_BIT);
    __delay_cycles(10);


    set_pru_bits(color_bits);
    __delay_cycles(10);

    set_pru_bits(CLK_BIT);
    __delay_cycles(10);

    clear_pru_bits(CLK_BIT);
   
    clear_pru_bits(CLEAR_COLOR_BITS); //added for matrix funkiness
}

void write_row_pins(uint32_t* gpio_bank, uint8_t row) 
{
    uint8_t a = row & 0x1;
    uint8_t b = (row & 0x2) > 1;
    uint8_t c = (row & 0x4) > 2;
    uint8_t d = (row & 0x8) > 3;
    uint32_t gpio_bits = a << GPIO_A | b << GPIO_B | c << GPIO_C | d << GPIO_D;
    uint32_t clear_bits = 1 << GPIO_A | 1 << GPIO_B | 1 << GPIO_C | 1 << GPIO_D;

    gpio_bank[GPIO_CLEARDATAOUT] = clear_bits;	// Clear all bits
    gpio_bank[GPIO_SETDATAOUT] = gpio_bits;	// set bits

}


void latch_and_enable(uint32_t* gpio_ports[4], uint32_t delay_ns)
{
    gpio_ports[GPIO_PORT_LATCH][GPIO_SETDATAOUT] = LATCH_BIT;
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;
    __delay_cycles(10);

    gpio_ports[GPIO_PORT_LATCH][GPIO_CLEARDATAOUT] = LATCH_BIT;
    __delay_cycles(10);

    gpio_ports[GPIO_PORT_OE][GPIO_CLEARDATAOUT] = OE_BIT;
    __delay_cycles(10);

    //200 MHz -> 5ns/cycle
    uint32_t delay_iter_x100 = delay_ns / 5 / 100;
    uint32_t i = 0;
    for (i = 0; i < delay_iter_x100; i++) {
        __delay_cycles(1000000);
    }
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;

}


void display_row(uint32_t delay_ns, uint8_t row_counter, uint8_t bit, \
        char* red_row1, char* green_row1, char* blue_row1, \
        char* red_row2, char* green_row2, char* blue_row2)
{
    uint8_t r1, g1, b1, r2, g2, b2;
    uint32_t* ports[4] = {(uint32_t *)GPIO0, (uint32_t *)GPIO1, (uint32_t *)GPIO2, (uint32_t *)GPIO3};
    write_row_pins(ports[GPIO_PORT_A], row_counter);
    
    uint8_t col = N_COL;
    for ( ; col > 0; col--)
    {
        r1 = (red_row1[col] & (1 << bit)) >> bit;//FIXME; is this arithmetic or logical shift? 
        g1 = (green_row1[col] & (1 << bit)) >> bit;
        b1 = (blue_row1[col] & (1 << bit)) >> bit;
        r2 = (red_row2[col] & (1 << bit)) >> bit;
        g2 = (green_row2[col] & (1 << bit)) >> bit;
        b2 = (blue_row2[col] & (1 << bit)) >> bit;
        write_color_bits(r1, g1, b1, r2, g2, b2);
    }

    latch_and_enable(ports, delay_ns);

}
