GOB SGI SUCCESS AND FAIL STATES by EDWARD HERROD (104541862)
Ensure you have a working version of Python 3.x installed.

Run the two files. Notice that the "success" file runs properly as intended and the SGI will complete its tasks. For simple scenarios like this without any environment or side-effects, SGI works fine;
However, the "fail" program will oscillate endlessly because side-effects to eating and sleeping have been added to increase one when the other is performed. This is a major weakness of SGI and demonstrates why it isn't ideal for more complex (i.e. realistic) scenarios...