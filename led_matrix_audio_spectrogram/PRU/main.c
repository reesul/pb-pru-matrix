#include <stdint.h>
#include <stdio.h>
#include <pru_cfg.h>
#include <pru_intc.h>
#include <rsc_types.h>
#include <pru_rpmsg.h>
#include "resource_table_0.h"
#include "prugpio.h"



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
/// The por for pins A-D, not ports
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

#define N_CHAN 3
#define N_ROW 32
#define N_COL 64

#define PRU_ADDR        0x4A300000      // Start of PRU memory Page 184 am335x TRM
#define PRU_LEN         0x80000         // Length of PRU memory
#define PRU0_DRAM       0x00000         // Offset to DRAM
#define PRU1_DRAM       0x02000
#define PRU_SHAREDMEM   0x10000         // Offset to shared memory
#define PRU_SRAM  __far __attribute__((cregister("PRU_SHAREDMEM", near)))

volatile register uint32_t __R30;
volatile register uint32_t __R31;

#define MD5_SUM_LEN_BYTES 16
#define EXTRA_OFFSET 0
volatile char *md5_image_host = (char*)PRU_SHAREDMEM;
//set to static location in DDR, which other programs will write to using /dev/mem
volatile char *image_base = (char*)PRU_SHAREDMEM + MD5_SUM_LEN_BYTES + EXTRA_OFFSET;
const int img_size = N_CHAN * N_ROW * N_COL;

#define RED_CHAN 0
#define GREEN_CHAN 1
#define BLUE_CHAN 2

typedef struct matrix_img {
	char mat[N_CHAN][N_ROW][N_COL];
} matrix_img_t;

// extern uint32_t* GPIO_PORTS[4];

#define DELAY_CYCLES_US (200)
#define DELAY_CYCLES_100NS (20)
#define DELAY_CYCLES_10NS (2)
#define DELAY_CYCLES_MS (200000)
#define DELAY_CYCLES_100MS (20000000)
#define DELAY_CYCLES_1S (200000000)

#define DELAY_CYCLES_DIMMER (DELAY_CYCLES_MS * 10)

#define MAX_COLOR_BITS (8)
#define COLOR_BITS (8)
#define UNUSED_COLOR_BITS ( MAX_COLOR_BITS - COLOR_BITS )
#define DELAY_NS_PER_BIT 20 // MSb at 10k was good for 1b depth, so 10*256 = 2,560 is probably okay. Total would be ~5120 ns = 5us per row. 10 is good starting value

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

uint8_t is_hash_same(char* local_md5, char* shared_md5)
{
	uint8_t i = 0;
	for ( ; i < MD5_SUM_LEN_BYTES; i++)
	{
		if (local_md5[i] != shared_md5[i])
		{
			return 0;
		}
	}
	return 1;
}

uint32_t sum_image_bits(matrix_img_t* img)
{
	int32_t sum = 0;
	int32_t i = 0;
	char* img_ptr = (char*) img;
	for (; i < N_CHAN*N_COL*N_ROW ; i++)
	{
		sum+= img_ptr[i];
		if ( i > 2*N_COL*N_ROW + N_COL*28 + (64-20)) break;
		// if ( i > 128 ) break;
	}
	return sum;
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
 * R1,G1, etc. are all boolean values (should be LSB bit only... not checking again in time critical code)
*/
void write_color_bits(uint8_t r1, uint8_t g1, uint8_t b1, \
        uint8_t r2, uint8_t g2, uint8_t b2)
{
    uint32_t color_bits = r1 << PRU_R1 | g1 << PRU_G1 | b1  << PRU_B1 |
        r2 << PRU_R2 | g2 << PRU_G2 | b2 <<PRU_B2;

    clear_pru_bits(CLEAR_COLOR_BITS); //make sure they are all in off state by default. No state from last iteration.

	/**Corect timing*/
	//ensure CLK is down
    clear_pru_bits(CLK_BIT);
    __delay_cycles(2);
	//set color signals
    set_pru_bits(color_bits);
    __delay_cycles(5);
	//rising clock
    set_pru_bits(CLK_BIT);
    __delay_cycles(5);
	//falling clock; color bits latch at this point
    clear_pru_bits(CLK_BIT);

	__delay_cycles(2);
   
    clear_pru_bits(CLEAR_COLOR_BITS); //added for matrix funkiness
}

void latch_and_enable(uint32_t* gpio_ports[4], uint32_t delay_ns)
{
    gpio_ports[GPIO_PORT_LATCH][GPIO_SETDATAOUT] = LATCH_BIT;
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;
    __delay_cycles(50); //50 cycles is sufficient

    gpio_ports[GPIO_PORT_LATCH][GPIO_CLEARDATAOUT] = LATCH_BIT;
    __delay_cycles(50);

    gpio_ports[GPIO_PORT_OE][GPIO_CLEARDATAOUT] = OE_BIT;
    __delay_cycles(50);

    //200 MHz -> 5ns/cycle
	// toggle_user_led_3_100ms(1);
    uint32_t delay_iter_10ns = delay_ns / 10;
    uint32_t i = 0;
    for (i = 0; i < delay_iter_10ns; i++) {
        __delay_cycles(DELAY_CYCLES_10NS);
    }
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;

}

void display_row(uint32_t delay_ns, uint8_t row_counter, uint8_t bit, \
        char* red_row1, char* green_row1, char* blue_row1, \
        char* red_row2, char* green_row2, char* blue_row2)
{
    uint32_t* ports[4] = {(uint32_t *)GPIO0, (uint32_t *)GPIO1, (uint32_t *)GPIO2, (uint32_t *)GPIO3};
    // uint8_t r1=0xff, g1=0xff, b1=0xff, r2=0xff, g2=0xff, b2=0xff;
    uint8_t r1, g1, b1, r2, g2, b2;

    write_row_pins(ports[GPIO_PORT_A], row_counter);
	// toggle_user_led_3_100ms(row_counter);

    int32_t col = N_COL-1;
	// bit = (bit <= 0 || bit > 7) ? 7 : bit;// clamp to 7 if not inside range
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

/*
 * main.c
 */
matrix_img_t active_image;


void main(void)
{
	char active_md5[MD5_SUM_LEN_BYTES];
	memset((void*)active_image.mat, 0xff, sizeof(active_image));
	//memset(active_md5, 0, sizeof(MD5_SUM_LEN_BYTES));
	toggle_user_led_3_100ms(1);
	__delay_cycles(DELAY_CYCLES_1S); 
	toggle_user_led_3_100ms(2);

	int16_t bit = 7; //highest bit for now 
	uint8_t row_counter = 15;
 
	while (1) {
		// __delay_cycles(DELAY_CYCLES_1S); 
		// toggle_user_led_3_100ms(1);

		if (!is_hash_same((char*)active_md5, (char*)md5_image_host))
		{
			
			//__delay_cycles(DELAY_CYCLES_1S); 
			//toggle_user_led_3_100ms(2);
			//__delay_cycles(DELAY_CYCLES_1S); 
			memset((void*)active_image.mat, 0, sizeof(active_image));
			memcpy((void*)active_image.mat, (void*)image_base, img_size);
			memcpy((void*)active_md5, (void*)md5_image_host, MD5_SUM_LEN_BYTES);

#ifdef CHECK_IMG_INTEGRITY
			int32_t sum_local, sum_shared;
			sum_local = sum_image_bits(&active_image);
			sum_shared = sum_image_bits((matrix_img_t*) image_base);

			if (sum_local != sum_shared) 
			{
				__delay_cycles(DELAY_CYCLES_100MS);
				// while(1);
			}
#endif
		}

		for (bit = MAX_COLOR_BITS-1; bit >= UNUSED_COLOR_BITS; bit--)
		{
	
			uint32_t delay_duration_ns = DELAY_NS_PER_BIT << bit;
			for (row_counter = 0; row_counter < N_ROW/2; row_counter++)
			{
				display_row( delay_duration_ns, row_counter, bit, \
					active_image.mat[RED_CHAN][row_counter], \
					active_image.mat[GREEN_CHAN][row_counter], \
					active_image.mat[BLUE_CHAN][row_counter], \
					active_image.mat[RED_CHAN][row_counter+N_ROW/2], \
					active_image.mat[GREEN_CHAN][row_counter+N_ROW/2], \
					active_image.mat[BLUE_CHAN][row_counter+N_ROW/2] );
					// active_image.mat[BLUE_CHAN][row_counter+N_ROW/2] );


			}
			//DEBUG CODE
			// toggle_user_led_3_100ms(bit+1);
			// __delay_cycles(DELAY_CYCLES_1S); 
		}
		//DEBUG CODE
		// __delay_cycles(DELAY_CYCLES_1S); 
		// toggle_user_led_3_100ms(20);
		// __delay_cycles(DELAY_CYCLES_1S); 

		__delay_cycles(DELAY_CYCLES_DIMMER);

	}

}
