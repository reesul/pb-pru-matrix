#warning "Found am335x"

//Memory map registers for GPIO banks
#define GPIO0 0x44E07000        // From table 2.2 of am335x TRM
#define GPIO1 0x4804C000
#define GPIO2 0x481AC000
#define GPIO3 0x481AE000

// USR LED bit positions
// GPIO1
#define USR0 (1<<21)
#define USR1 (1<<22)
#define USR2 (1<<23)
#define USR3 (1<<24)
// The define a couple of GPIO pin addresses on Black
// GPIO1
#define P9_14 (1<<18)
#define P9_16 (1<<19)

// The define a couple of GPIO pin addresses on Pocket
// GPIO1
#define P2_1 (1<<18)
#define P1_32 (1<<10)

// R30 output bits on pru0
#define P9_31   (1<<0)
#define P9_29   (1<<1)
#define P9_30   (1<<2)
#define P9_28   (1<<3)
#define P9_92   (1<<4)
#define P9_27   (1<<5)
#define P9_91   (1<<6)
#define P9_25   (1<<7)

// R30 output bits on pru0 on Pocket
#define P1_36   (1<<0)
#define P1_33   (1<<1)
#define P2_32   (1<<2)
#define P2_30   (1<<3)
#define P1_31   (1<<4)
#define P2_34   (1<<5)
#define P2_28   (1<<6)
#define P1_29   (1<<7)

// Shared memory
#define AM33XX_DATARAM0_PHYS_BASE		0x4a300000
#define AM33XX_DATARAM1_PHYS_BASE		0x4a302000
#define AM33XX_PRUSS_SHAREDRAM_BASE		0x4a310000

// /4 to convert from byte address to word address
#define GPIO_CLEARDATAOUT	0x190/4     // Write 1 here to set a given bit    
#define GPIO_SETDATAOUT 	0x194/4     // A 1 here clears the corresponding bit
#define GPIO_DATAOUT		0x138/4     // For reading the GPIO registers
