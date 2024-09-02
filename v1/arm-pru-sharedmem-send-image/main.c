/*
 * Copyright (C) 2018 Texas Instruments Incorporated - http://www.ti.com/
 *
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *	* Redistributions of source code must retain the above copyright
 *	  notice, this list of conditions and the following disclaimer.
 *
 *	* Redistributions in binary form must reproduce the above copyright
 *	  notice, this list of conditions and the following disclaimer in the
 *	  documentation and/or other materials provided with the
 *	  distribution.
 *
 *	* Neither the name of Texas Instruments Incorporated nor the names of
 *	  its contributors may be used to endorse or promote products derived
 *	  from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdint.h>
#include <stdio.h>
#include <pru_cfg.h>
#include <pru_intc.h>
#include <rsc_types.h>
#include <pru_rpmsg.h>
#include "resource_table_0.h"
#include "prugpio.h"
// #include <fcntl.h>
//#include <sys/mman.h>

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

/* Host-0 Interrupt sets bit 30 in register R31 */
#define HOST_INT			((uint32_t) 1 << 30)

/* The PRU-ICSS system events used for RPMsg are defined in the Linux device tree
 * PRU0 uses system event 16 (To ARM) and 17 (From ARM)
 * PRU1 uses system event 18 (To ARM) and 19 (From ARM)
 */
#define TO_ARM_HOST			16
#define FROM_ARM_HOST			17

/*
 * Using the name 'rpmsg-pru' will probe the rpmsg_pru driver found
 * at linux-x.y.z/drivers/rpmsg/rpmsg_pru.c
 */
#define CHAN_NAME			"rpmsg-pru"
#define CHAN_DESC			"Channel 30"
#define CHAN_PORT			30

/*
 * Used to make sure the Linux drivers are ready for RPMsg communication
 * Found at linux-x.y.z/include/uapi/linux/virtio_config.h
 */
#define VIRTIO_CONFIG_S_DRIVER_OK	4


#define RPMSG_BUF_HEADER_SIZE           16
uint8_t payload[RPMSG_BUF_SIZE - RPMSG_BUF_HEADER_SIZE]; //512 byte msg

/*
PRU_ADDR = 0x4A300000
PRU_SHARED_OFFSET = 0x10000
PRU_SHARED_LOC = PRU_ADDR + PRU_SHARED_OFFSET
*/
#define PRU_ADDR        0x4A300000      // Start of PRU memory Page 184 am335x TRM
#define PRU_LEN         0x80000         // Length of PRU memory
#define PRU0_DRAM       0x00000         // Offset to DRAM
#define PRU1_DRAM       0x02000
#define PRU_SHAREDMEM   0x10000         // Offset to shared memory
#define PRU_SRAM  __far __attribute__((cregister("PRU_SHAREDMEM", near)))

// uint32_t    *pru0DRAM_32int_ptr;        // Points to the start of local DRAM
// unsigned uint32_t    *pru1DRAM_32int_ptr;        // Points to the start of local DRAM
// unsigned uint32_t    *prusharedMem_32int_ptr;    // Points to the start of the shared memory

volatile register uint32_t __R30;
volatile register uint32_t __R31;

#define MD5_SUM_LEN_BYTES 16
#define EXTRA_OFFSET 0
volatile char *md5_image_host = (char*)PRU_SHAREDMEM;

volatile char *image_base = (char*)PRU_SHAREDMEM + MD5_SUM_LEN_BYTES + EXTRA_OFFSET;

// char* active_md5 = (char *) (PRU0_DRAM + 0x200);
// char* active_image[N_CHAN][N_ROW][N_COL] = (char *) (PRU0_DRAM + 0x210);
// char active_image[N_CHAN][N_ROW][N_COL];// = (char(*)[N_CHAN][N_ROW][N_COL]) (PRU0_DRAM + 0x210);
// char* active_image = (char *) (PRU0_DRAM + 0x210);
const int img_size = N_CHAN * N_ROW * N_COL;

#define RED_CHAN 0
#define GREEN_CHAN 1
#define BLUE_CHAN 2

typedef struct matrix_img {
	char mat[N_CHAN][N_ROW][N_COL];
} matrix_img_t;

// extern uint32_t* GPIO_PORTS[4];

#define DELAY_CYCLES_US (200)
#define DELAY_CYCLES_MS (200000)
#define DELAY_CYCLES_100MS (20000000)
#define DELAY_CYCLES_1S (200000000)

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
   	// wait

	// __delay_cycles(cycles>>1); 
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
   	// wait

	// __delay_cycles(cycles>>1); 
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

static inline void set_pru_bits(uint32_t data)
{
    __R30 |= data;
}

static inline void clear_pru_bits(uint32_t data)
{
    __R30 &= ~data;
}

const uint32_t CLEAR_COLOR_BITS_l = 1 << PRU_R1 | 1 << PRU_G1 | 1  << PRU_B1 | 1 << PRU_R2 | 1 << PRU_G2 | 1 <<PRU_B2;

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

void write_color_bits(uint8_t r1, uint8_t g1, uint8_t b1, \
        uint8_t r2, uint8_t g2, uint8_t b2)
{
    uint32_t color_bits = r1 << PRU_R1 | g1 << PRU_G1 | b1  << PRU_B1 |
        r2 << PRU_R2 | g2 << PRU_G2 | b2 <<PRU_B2;

    clear_pru_bits(CLEAR_COLOR_BITS_l); //make sure they are all in off state by default. No state from last iteration.
    __delay_cycles(10);    
    clear_pru_bits(CLK_BIT);
    __delay_cycles(10);


    set_pru_bits(color_bits);
    __delay_cycles(10);

    set_pru_bits(CLK_BIT);
    __delay_cycles(10);

    clear_pru_bits(CLK_BIT);

	__delay_cycles(10);

   
    clear_pru_bits(CLEAR_COLOR_BITS_l); //added for matrix funkiness
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
	// toggle_user_led_3_100ms(1);
    uint32_t delay_iter_us = delay_ns / 1000;
    uint32_t i = 0;
    for (i = 0; i < delay_iter_us; i++) {
        __delay_cycles(DELAY_CYCLES_US);
    }
    gpio_ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;

}

void display_row(uint32_t delay_ns, uint8_t row_counter, uint8_t bit, \
        char* red_row1, char* green_row1, char* blue_row1, \
        char* red_row2, char* green_row2, char* blue_row2)
{
    uint8_t r1=0xff, g1=0xff, b1=0xff, r2=0xff, g2=0xff, b2=0xff;
    uint32_t* ports[4] = {(uint32_t *)GPIO0, (uint32_t *)GPIO1, (uint32_t *)GPIO2, (uint32_t *)GPIO3};
    write_row_pins(ports[GPIO_PORT_A], row_counter);
	// toggle_user_led_3_100ms(row_counter);

    int8_t col = N_COL-1;
    for ( ; col >= 0; col--)
    {
        r1 = (red_row1[col] & (1 << bit)) >> bit;//FIXME; is this arithmetic or logical shift? 
        g1 = (green_row1[col] & (1 << bit)) >> bit;
        b1 = (blue_row1[col] & (1 << bit)) >> bit;
        r2 = (red_row2[col] & (1 << bit)) >> bit;
        g2 = (green_row2[col] & (1 << bit)) >> bit;
        b2 = (blue_row2[col] & (1 << bit)) >> bit;
		// if (row_counter >8 && col > 33) {
		// 	b2 = 1;
		// }
        write_color_bits(r1, g1, b1, r2, g2, b2);
		// write_color_bits(r1, g1, b1, r2, g2, b2);

    }

    latch_and_enable(ports, delay_ns);

}

/*
 * main.c
 */
void main(void)
{
	char active_md5[MD5_SUM_LEN_BYTES];
	matrix_img_t active_image;
	memset((void*)active_image.mat, 0xff, sizeof(active_image));
	// char active_image[N_CHAN][N_ROW][N_ROW] = {0xff};//= (char (*)[N_CHAN][N_ROW][N_COL]) active_image;
	//memset(active_image, 0xff, sizeof(active_image));
	//memset(active_md5, 0, sizeof(MD5_SUM_LEN_BYTES));
	toggle_user_led_3_100ms(1);
	__delay_cycles(DELAY_CYCLES_1S); 
	toggle_user_led_3_100ms(1);

	uint8_t bit = 7; //highest bit for now 
	uint8_t row_counter = 15;
	uint32_t delay_ns_high_bit = 1000 * 10; //5ms is ok; 10us shows 'static' image

	uint32_t *gpio0 = (uint32_t *)GPIO0;
    uint32_t *gpio1 = (uint32_t *)GPIO1;
    uint32_t *gpio2 = (uint32_t *)GPIO2;
    uint32_t *gpio3 = (uint32_t *)GPIO3;

    uint32_t* ports[4] = {gpio0, gpio1, gpio2, gpio3};
 
	while (1) {
		// __delay_cycles(DELAY_CYCLES_1S); 
		// toggle_user_led_3_100ms(1);

		if (!is_hash_same((char*)active_md5, (char*)md5_image_host) || 1)
		{
			//__delay_cycles(DELAY_CYCLES_1S); 
			//toggle_user_led_3_100ms(2);
			//__delay_cycles(DELAY_CYCLES_1S); 
			memset((void*)active_image.mat, 0, sizeof(active_image));
			memcpy((void*)active_image.mat, (void*)image_base, img_size);
			memcpy((void*)active_md5, (void*)md5_image_host, MD5_SUM_LEN_BYTES);
		}

		for (row_counter = 0; row_counter < N_ROW/2; row_counter++)
		{
			display_row( delay_ns_high_bit, row_counter, bit, \
				active_image.mat[RED_CHAN][row_counter], active_image.mat[GREEN_CHAN][row_counter], active_image.mat[BLUE_CHAN][row_counter], \
				active_image.mat[RED_CHAN][row_counter+N_ROW/2], active_image.mat[GREEN_CHAN][row_counter+N_ROW/2], active_image.mat[BLUE_CHAN][row_counter+N_ROW/2] );
			// toggle_user_led_3_100ms(row_counter);

			// display_row( delay_ns_high_bit, row_counter, bit, \
			// 	BASE_ROW, BASE_ROW, BASE_ROW, BASE_ROW, BASE_ROW, BASE_ROW);
		
			// write_row_pins((uint32_t *)GPIO1, 0);
			// uint8_t a = row_counter & 0x1;
			// uint8_t b = (row_counter & 0x2) > 1;
			// uint8_t c = (row_counter & 0x4) > 2;
			// uint8_t d = (row_counter & 0x8) > 3;
			// uint32_t gpio_bits = a << GPIO_A | b << GPIO_B | c << GPIO_C | d << GPIO_D;
			// uint32_t clear_bits = 1 << GPIO_A | 1 << GPIO_B | 1 << GPIO_C | 1 << GPIO_D;


			// ports[GPIO_PORT_A][GPIO_CLEARDATAOUT] = clear_bits;	// Clear all bits
			// ports[GPIO_PORT_A][GPIO_SETDATAOUT] = gpio_bits;	// set bits
			// //row pins
			// int8_t col = 0;
			// for ( ; col <N_COL ; col++)
			// {
			// 	// toggle_user_led_3_100ms(1);
			// 	write_color_bits(1, 1, 1, 1, 1, 1);
			// }
			// latch_and_enable(ports, delay_ns_high_bit);
			// ports[GPIO_PORT_LATCH][GPIO_SETDATAOUT] = LATCH_BIT;
			// ports[GPIO_PORT_OE][GPIO_SETDATAOUT] = OE_BIT;
			// __delay_cycles(10);

			// ports[GPIO_PORT_LATCH][GPIO_CLEARDATAOUT] = LATCH_BIT;
			// __delay_cycles(10);

			// ports[GPIO_PORT_OE][GPIO_CLEARDATAOUT] = OE_BIT;
			// __delay_cycles(10);
			// __delay_cycles(10000000);


			// __delay_cycles(20000000); 
			// toggle_user_led_3_100ms(3);
			// __delay_cycles(20000000); 


		}
	
	}
		

}
