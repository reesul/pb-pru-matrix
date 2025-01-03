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

// uint32_t    *pru0DRAM_32int_ptr;        // Points to the start of local DRAM
// unsigned uint32_t    *pru1DRAM_32int_ptr;        // Points to the start of local DRAM
// unsigned uint32_t    *prusharedMem_32int_ptr;    // Points to the start of the shared memory


volatile register uint32_t __R31;


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

/**
 * time = cycle/200M(Hz)
 * 500ms = 100000000
*/
void slow_toggle_user_led_3()
{
	uint32_t *gpio1 = (uint32_t *)GPIO1;

	gpio1[GPIO_SETDATAOUT]   = USR3;	// The the USR3 LED on
	__delay_cycles(100000000);    	// wait
	gpio1[GPIO_CLEARDATAOUT] = USR3;

	// __delay_cycles(cycles>>1); 
}

void fast_toggle_user_led_3()
{
	uint32_t *gpio1 = (uint32_t *)GPIO1;

	gpio1[GPIO_SETDATAOUT]   = USR3;	// The the USR3 LED on
	__delay_cycles(10000000);    	// wait
	gpio1[GPIO_CLEARDATAOUT] = USR3;

	// __delay_cycles(cycles>>1); 
}

/*
 * main.c
 */
void main(void)
{
	struct pru_rpmsg_transport transport;
	uint16_t src, dst, len;
	volatile uint8_t *status;

	//GPIO1_24 is user LED 3
	// uint32_t *gpio1 = (uint32_t *)GPIO1;

	/* Allow OCP master port access by the PRU so the PRU can read external memories */
	CT_CFG.SYSCFG_bit.STANDBY_INIT = 0;

	/* Clear the status of the PRU-ICSS system event that the ARM will use to 'kick' us */
	CT_INTC.SICR_bit.STS_CLR_IDX = FROM_ARM_HOST;

	/* Make sure the Linux drivers are ready for RPMsg communication */
	status = &resourceTable.rpmsg_vdev.status;
	while (!(*status & VIRTIO_CONFIG_S_DRIVER_OK));

	/* Initialize the RPMsg transport structure */
	pru_rpmsg_init(&transport, &resourceTable.rpmsg_vring0, &resourceTable.rpmsg_vring1, TO_ARM_HOST, FROM_ARM_HOST);

	/* Create the RPMsg channel between the PRU and ARM user space using the transport structure. */
	while (pru_rpmsg_channel(RPMSG_NS_CREATE, &transport, CHAN_NAME, CHAN_DESC, CHAN_PORT) != PRU_RPMSG_SUCCESS);

	while (1) {
		/* Check bit 30 of register R31 to see if the ARM has kicked us */
		// continue;
		if (__R31 & HOST_INT) {
			/* Clear the event status */

			CT_INTC.SICR_bit.STS_CLR_IDX = FROM_ARM_HOST;
			/* Receive all available messages, multiple messages can be sent per kick */
			slow_toggle_user_led_3();
			__delay_cycles(100000000);

			while (pru_rpmsg_receive(&transport, &src, &dst, payload, &len) == PRU_RPMSG_SUCCESS) {
				/* Echo the message back to the same address from which we just received */
				//pru_rpmsg_send(&transport, dst, src, payload, len);
				toggle_user_led_3_100ms(payload[0]);
				__delay_cycles(10000000);
			}
			__delay_cycles(100000000);

		}
	}
}
