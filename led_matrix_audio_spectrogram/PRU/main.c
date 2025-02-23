// Provided as-is with no guarantees. Use and extend as you like. MIT license
// Reese Grimsley, 2025
#include <stdint.h>
#include <stdio.h>
#include <pru_cfg.h>
#include <pru_intc.h>
#include <rsc_types.h>
#include <pru_rpmsg.h>
#include "resource_table_0.h"
#include "prugpio.h"

// define some timing based on 200 MHz clock. Have 5ns granularity at best
#define DELAY_CYCLES_US (200)
#define DELAY_CYCLES_100NS (20)
#define DELAY_CYCLES_10NS (2)
#define DELAY_CYCLES_MS (200000)
#define DELAY_CYCLES_100MS (20000000)
#define DELAY_CYCLES_1S (200000000)

// Used to further dim the display by having some additional 'waits'
// May impact responsiveness / framerate
#define USE_DIMMER 0
#define DELAY_CYCLES_DIMMER (DELAY_CYCLES_MS * 5)


#define MAX_COLOR_BITS (8) //cannot go above this without changing datatype of matrix_img
#define COLOR_BITS (6)
#define UNUSED_COLOR_BITS ( MAX_COLOR_BITS - COLOR_BITS )

//how much time we'll wait for each bit (*2^bit0). If too low, then low-order bits will be effectively useless by overhead. We only have 5ns / cycle
#define DELAY_NS_PER_BIT 40 


// defines for PRU pins / bits for color control
#define PRU_R1 1
#define PRU_G1 7
#define PRU_B1 4
#define PRU_R2 3
#define PRU_G2 5
#define PRU_B2 2
#define PRU_CLK 6
#define R1_BIT 1<<PRU_G1
#define G1_BIT 1<<PRU_B1
#define B1_BIT 1<<PRU_R2
#define R2_BIT 1<<PRU_R1
#define G2_BIT 1<<PRU_G2
#define B2_BIT 1<<PRU_B2
#define CLK_BIT 1<<PRU_CLK

// GPIO defines for pins
/// Tdefine the GPIO port and the pin within that port
#define GPIO_PORT_A 1
#define GPIO_PORT_B 1
#define GPIO_PORT_C 1
#define GPIO_PORT_D 1
#define GPIO_PORT_LATCH 2
#define GPIO_PORT_OE 1
#define GPIO_A 27
#define GPIO_B 26
#define GPIO_C 25
#define GPIO_D 28
#define GPIO_LATCH 0
#define GPIO_OE 14
#define LATCH_BIT  1<<GPIO_LATCH
#define OE_BIT  1<<GPIO_OE

// size of the LED matrix and the data-structure holding its pixel value
#define MAT_SIZE_N_CHAN 3
#define MAT_SIZE_N_ROW 32
#define MAT_SIZE_N_COL 64


#define PRU_ADDR        0x4A300000      // Start of PRU memory Page 184 am335x TRM
#define PRU_LEN         0x80000         // Length of PRU memory
#define PRU0_DRAM       0x00000         // Offset to DRAM
#define PRU1_DRAM       0x02000
#define PRU_SHAREDMEM   0x10000         // Offset to shared memory
#define PRU_SRAM  __far __attribute__((cregister("PRU_SHAREDMEM", near)))
//TODO: add DDR so that can be used explicitly too

// Specific re-defs of PRU registers that are used as input/output for PRU pins. 
// Can also be used for some interrupt signals
volatile register uint32_t __R30; //used for output
volatile register uint32_t __R31; //used for input

// MD5 sum is used as a check for a new image we'll use a 128-bit hash
#define MD5_SUM_LEN_BYTES 16

// We'll use the entire PRU SRAM for this image (but should migrate to using DDR region)
volatile char *md5_image_host = (char*)PRU_SHAREDMEM;
//set to static location in DDR, which other programs will write to using /dev/mem
volatile char *image_base = (char*)PRU_SHAREDMEM + MD5_SUM_LEN_BYTES ;
const int img_size = MAT_SIZE_N_CHAN * MAT_SIZE_N_ROW * MAT_SIZE_N_COL;

// somewhat important because OpenCV prefers BGR by default. considering switching to eliminate overhead of BGR2RGB
#define RED_CHAN 0
#define GREEN_CHAN 1
#define BLUE_CHAN 2

typedef struct matrix_img {
	char mat[MAT_SIZE_N_CHAN][MAT_SIZE_N_ROW][MAT_SIZE_N_COL];
} matrix_img_t;

// Use for signalling and debugging
void toggle_user_led_3_1ms(int n)
{
	int i = 0;
	uint32_t *gpio1 = (uint32_t *)GPIO1;

	for ( i = 0; i < n ; i++)
	{
		gpio1[GPIO_SETDATAOUT]   = USR3;	// The the USR3 LED on
		__delay_cycles(100000);    	// wait
		gpio1[GPIO_CLEARDATAOUT] = USR3;
		__delay_cycles(100000); 
	}
}

//used for signalling and debugging
void toggle_user_led_3_100ms(int n)
{
	int i = 0;
	uint32_t *gpio1 = (uint32_t *)GPIO1;

	for ( i = 0; i < n ; i++)
	{
		gpio1[GPIO_SETDATAOUT]   = USR3;	// The the USR3 LED on
		__delay_cycles(10000000);    	// wait
		gpio1[GPIO_CLEARDATAOUT] = USR3;
		__delay_cycles(10000000); 
	}
}

// check for hash equality
uint8_t is_hash_same(char* local_md5, char* shared_md5, uint32_t hash_size)
{
	uint8_t i = 0;
	uint8_t same = 1;
	for ( ; i < hash_size; i++)
	{
		if (local_md5[i] != shared_md5[i])
		{
			same = 0;
		}
	}
	return same;
}


static inline void set_pru_bits(uint32_t data)
{
    __R30 |= data;
}

static inline void clear_pru_bits(uint32_t data)
{
    __R30 &= ~data;
}

const uint32_t CLEAR_COLOR_BITS = 1 << PRU_R1 | 1 << PRU_G1 | 1  << PRU_B1 | 1 << PRU_R2 | 1 << PRU_G2 | 1 <<PRU_B2;

// Write A,B,C,D output pins that dictate which rows are being controlled. 
//   Matrix is given 4 control lines, but 32 rows, so two rows are actually active at once (n, n+16)
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

/**
 * Write the actual data bits to PRU pins. Data is set on falling edge of clock
 * Assume R1,G1, etc. are all boolean values (should be LSB bit only... not checking again in time critical code)
*/
void write_color_bits(uint8_t r1, uint8_t g1, uint8_t b1, \
        uint8_t r2, uint8_t g2, uint8_t b2)
{
    uint32_t color_bits = r1 << PRU_R1 | g1 << PRU_G1 | b1  << PRU_B1 |
        r2 << PRU_R2 | g2 << PRU_G2 | b2 <<PRU_B2;

    clear_pru_bits(CLEAR_COLOR_BITS); //make sure they are all in off state by default. No state from last iteration.

	//ensure CLK is down; empirically, this is skippable
    // clear_pru_bits(CLK_BIT);
    // __delay_cycles(2);
	//set color signals
    set_pru_bits(color_bits);
    __delay_cycles(3);
	//rising clock
    set_pru_bits(CLK_BIT);
    __delay_cycles(3);
	//falling clock; color bits latch at this point
    clear_pru_bits(CLK_BIT);

	__delay_cycles(3);
   
    clear_pru_bits(CLEAR_COLOR_BITS); //added for matrix funkiness
}


// Signals actual output to the LEDs. Latch the data and set (not) Output-enable
void latch_and_enable(uint32_t* gpio_ports[4], uint32_t delay_ns)
{
    gpio_ports[GPIO_PORT_LATCH][GPIO_SETDATAOUT] = LATCH_BIT;
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;
    __delay_cycles(10); //10 cycles is sufficient; GPIO is slower

    gpio_ports[GPIO_PORT_LATCH][GPIO_CLEARDATAOUT] = LATCH_BIT;
    __delay_cycles(10);

	//OE going low will cause the data to actually be written out
    gpio_ports[GPIO_PORT_OE][GPIO_CLEARDATAOUT] = OE_BIT;
    __delay_cycles(10);

    //200 MHz -> 5ns/cycle
    uint32_t delay_iter_10ns = delay_ns / 10;
    uint32_t i = 0;
    for (i = 0; i < delay_iter_10ns; i++) { //at least 2 cycles overhead, right?
        __delay_cycles(DELAY_CYCLES_10NS);
    }
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;

}


// Display a row for delay_ns for row row_counter, row_counter+(MAT_ROW/2)
// provide a pointer to the bytes for the rows in question, for each color channel
void display_row(uint32_t delay_ns, uint8_t row_counter, uint8_t bit, \
        char* red_row1, char* green_row1, char* blue_row1, \
        char* red_row2, char* green_row2, char* blue_row2)
{
    uint32_t* ports[4] = {(uint32_t *)GPIO0, (uint32_t *)GPIO1, (uint32_t *)GPIO2, (uint32_t *)GPIO3};
    // uint8_t r1=0xff, g1=0xff, b1=0xff, r2=0xff, g2=0xff, b2=0xff;
    uint8_t r1, g1, b1, r2, g2, b2;

    write_row_pins(ports[GPIO_PORT_A], row_counter);

    int32_t col = MAT_SIZE_N_COL-1;
	// bits will be piped in starting from the furthest column
    for ( ; col >= 0; col--)
    {
		// for each pixel, isolate the current bit
		r1 = ( (red_row1[col]) >> bit ) & 0x1;
        g1 = ( (green_row1[col]) >> bit ) & 0x1;
        b1 = ( (blue_row1[col]) >> bit ) & 0x1;
        r2 = ( (red_row2[col]) >> bit ) & 0x1;
        g2 = ( (green_row2[col]) >> bit ) & 0x1;
        b2 = ( (blue_row2[col]) >> bit ) & 0x1;
		
        write_color_bits(r1, g1, b1, r2, g2, b2);

    }

    latch_and_enable(ports, delay_ns);
}


matrix_img_t active_image;


void main(void)
{
	char active_md5[MD5_SUM_LEN_BYTES];
	memset((void*)active_image.mat, 0xff, sizeof(active_image));

	//startup signalling to LED
	toggle_user_led_3_100ms(1);
	__delay_cycles(DELAY_CYCLES_1S); 
	toggle_user_led_3_100ms(2);

	int16_t bit = 7; //highest bit for now 
	uint8_t row_counter = 15;
 
	while (1) {
		// Check for a new image by comparing the current md5sum of the image with one in staging area
		if (!is_hash_same((char*)active_md5, (char*)md5_image_host, MD5_SUM_LEN_BYTES))
		{
			
			memset((void*)active_image.mat, 0, sizeof(active_image));
			memcpy((void*)active_image.mat, (void*)image_base, img_size);
			memcpy((void*)active_md5, (void*)md5_image_host, MD5_SUM_LEN_BYTES);

		}

		// Iterate over the bits we want to address, starting from the highest-order bit
		for (bit = MAX_COLOR_BITS-1; bit >= UNUSED_COLOR_BITS; bit--)
		{
	
			uint32_t delay_duration_ns = DELAY_NS_PER_BIT << bit;
			//Display 2 rows at a time
			for (row_counter = 0; row_counter < MAT_SIZE_N_ROW/2; row_counter++)
			{
				display_row( delay_duration_ns, row_counter, bit, \
					active_image.mat[RED_CHAN][row_counter], \
					active_image.mat[GREEN_CHAN][row_counter], \
					active_image.mat[BLUE_CHAN][row_counter], \
					active_image.mat[RED_CHAN][row_counter + MAT_SIZE_N_ROW/2], \
					active_image.mat[GREEN_CHAN][row_counter + MAT_SIZE_N_ROW/2], \
					active_image.mat[BLUE_CHAN][row_counter + MAT_SIZE_N_ROW/2] );
					// active_image.mat[BLUE_CHAN][row_counter+MAT_SIZE_N_ROW/2] );


			}
		}

#if USE_DIMMER
		__delay_cycles(DELAY_CYCLES_DIMMER);
#endif
	}

}
