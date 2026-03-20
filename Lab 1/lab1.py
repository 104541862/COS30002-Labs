# import libraries
import random
import time

# setup variables
nrg = 100
mon = 100
ore = 0

# setup states (start off by drilling)
drilling = True
recharging = False
selling = False

# function which prints all variables to terminal
def print_vars(nrg, mon, ore):
    print(f"Energy: {nrg}\nMoney: ${mon:.2f}\nOre: {ore}")

# drilling reduces energy but gains ore
def drill(nrg, ore):
    ore += 1
    nrg -= 1
    print_vars(nrg, mon, ore)
    return nrg, ore

# recharging reduces money but gains energy
def recharge(nrg, mon):
    nrg += 1
    mon -= 1
    print_vars(nrg, mon, ore)
    return nrg, mon

# selling reduces ore but gains money
def sell(mon, ore):
    mon += random.uniform(0.1, 3)
    ore -= 1
    print_vars(nrg, mon, ore)
    return mon, ore

# run this each frame - checks variables and runs whatever action is necessary depending on state
def update(nrg, mon, ore, drilling, recharging, selling):
    if recharging:
        nrg, mon = recharge(nrg, mon)
        if nrg == 100:
            recharging = False
            drilling = True
            print("Drilling ore...")
    elif drilling:
        nrg, ore = drill(nrg, ore)
        if nrg == 5:
            drilling = False
            recharging = True
            print("Recharging batteries...")
        elif ore >= 100:
            drilling = False
            selling = True
            print("Selling ore...")
    elif selling:
        mon, ore = sell(mon, ore)
        if ore == 0:
            selling = False
            drilling = True
            print("Drilling ore...")
    return nrg, mon, ore, drilling, recharging, selling

# FSM loop (0.2 second ticks so that what's happening is discernable)
while True:
    nrg, mon, ore, drilling, recharging, selling = update(nrg, mon, ore, drilling, recharging, selling)
    time.sleep(0.5)

