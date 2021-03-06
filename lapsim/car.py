import math # sin

gravity = 9.81 # m/s^2

class Car:
    """A class representing the solar car
    
    This class stores all characteristics of the car, such as the battery levels and dynamic
    coefficients. It has access to race strategy functions that can determine desired speeds
    based on certain conditions, as well as functions to update values of the car
    such as capacity or energy.

    Attributes:
        max_speed: an int representing the fastest speed the car can reach
        start_soc: a percentage representing the starting state of charge of the batteries
        end_soc: a percentage representing the desired end state of charge of the batteries
        capacity: an int of the total capacity of the batteries in KWh
        mass: an int of the mass of the car in kg 
        rolling_resistance: a float of the rolling resistance constant of the car
        drag_c: a float of the drag coefficient of the car
        cross_area: a float of the front cross sectional area of the car in m^2
        recharge_rate: a float representing how much power the solar cells generate in KWh
        current_capacity: a float that stores the current capacity of the batteries during the simulation in KWh
        end_capacity: a float that stores the desired end capacity of the batteries in KWh
    """
    def __init__(self, inputs, recharge_rate = 0.8):

        self.max_speed          = int(inputs["max_speed"]) # kph
        self.start_soc          = inputs["start_soc"] # %, soc = state of charge
        self.end_soc            = inputs["end_soc"] # %, what we want the soc to be at the end
        self.capacity           = inputs["capacity"] # KWh
        self.mass               = inputs["mass"] # kg
        self.rolling_resistance = inputs["rolling_resistance"] # average for car tires on asphalt
        self.drag_c             = inputs["drag_coefficient"] # from thiago
        self.cross_area         = inputs["cross_area"] # m^2, from thiago
        self.recharge_rate      = recharge_rate

        self.current_capacity   = (self.start_soc * self.capacity) / 100 # KWh
        self.end_capacity       = (self.end_soc   * self.capacity) / 100 # KWh
    

    # gives the best speed we can run
    def best_speed(self, distance, angle):
        """
        Takes a distance and calculates the best speed the car can currently drive at.
        
        Args:
            distance: A value indicating the distance to calculate the speed with.
        
        Returns:
            A speed, in kph, that the car should travel at to achieve maximum efficiency.
        """
        acceleration   = 0
        air_density    = 1.225 # kg/m^3

        for velocity in range(self.max_speed, 0, -1): # velocity in km/h
            time = distance / velocity
            gained_energy = self.recharge_rate * time # KWh 
            energy = self.motor_energy(velocity, distance, angle)
            # energy = (1/3600) * distance * ((self.mass * gravity * self.rolling_resistance) +
            #         (0.0386 * air_density * self.drag_c * self.cross_area * velocity ** 2) + # 0.0386 for km/h
            #         (self.mass * acceleration))

            if (self.current_capacity - energy + gained_energy) >= self.end_capacity:
                return velocity
    

    def coast_speed(self, distance, angle):
        """
        Takes a distance and calculates the best coasting speed the car can currently drive at. 
        This speed will be something within the range of being able to power the car 
        on mainly solar power so the battery is able to recharge while driving.
        
        Args:
            distance: A value indicating the distance to calculate the speed with.
        
        Returns:
            A speed, in kph, that the car should travel at to recharge its batteries with.
        """
        acceleration   = 0
        air_density    = 1.225 # kg/m^3

        # if (abs(angle) > 0.5): # big road grade change
        #     flat_v = self.coast_speed(distance, 0)
        #     flat_energy = self.motor_energy(flat_v, distance, 0)
        #     for velocity in range(1, self.max_speed):
        #         test_energy = self.motor_energy(velocity, distance, angle)
        #         if (abs(flat_energy - test_energy) <= 0.00001):
        #             print(f"{flat_energy}, {test_energy}")
        #             return velocity
            
        for velocity in range(1, self.max_speed): # velocity in km/h
            time = distance / velocity
            gained_energy = self.recharge_rate * time # KWh 
            energy = self.motor_energy(velocity, distance, angle)
            # energy = (1/3600) * distance * ((self.mass * gravity * self.rolling_resistance) +
            #         (0.0386 * air_density * self.drag_c * self.cross_area * velocity ** 2) + # 0.0386 for km/h
            #         (self.mass * acceleration))

            if (energy >= gained_energy): # find best coasting speed
                print("found velocity")
                return velocity - 5
        print("returning max speed")
        return self.max_speed


    # return time to recharge battery while coasting(default charges to 80%)
    def calc_recharge_time(self, upper_battery_capacity = 4, lap_length = 5, distance = 5, angle = 0):
        """
        Takes a total distance and calculates the time it would take for the car 
        to recharge its batteries to the given capacity. Assumes that 
        the car is travelling at the optimized coasting speed
        
        Args:
            upper_battery_capacity: The battery capacity the car should recharge to.
            lap_length: The distance of one lap, in km.
            distance: The total distance for the car to travel, in km.
        
        Returns:
            A time, in hours, that the car would take to recharge its batteries while driving.
        
        """
        coasting_velocity = self.coast_speed(lap_length, angle) # KWh, point when to swap back to battery power
        time  = ((upper_battery_capacity - self.current_capacity) / 
                (self.recharge_rate - self.motor_energy(coasting_velocity, distance, 0)))
        return time


    def update_capacity(self, curr_velocity, distance, angle):
        """
        Takes the current velocity the car is travelling at and a distance that 
        the car travelled over to calculate how much power was used. This updates
        the current capacity of the car acccordingly.
        
        Args:
            curr_velocity: The current velocity that the car is driving at.
            distance: The distance that the car travelled within this section, in km.
        
        """
        time = distance / curr_velocity

        gained_energy = self.recharge_rate * time # KWh 
        
        energy = self.motor_energy(curr_velocity, distance, angle)
        self.current_capacity += gained_energy - energy


    ### DYNAMICS EQUATIONS ###

    def motor_energy(self, velocity, distance, angle):
        """
        Uses a velocity, distance, and gradient angle of the road to determine
        how much power is needed to drive the motor.

        This calculates the power needed based on rolling resistance, hill climbing,
        and air drag for the vehicle.
        
        Args:
            velocity: The desired speed the car should travel at.
            distance: The distance to travel at the given speed.
            angle: The gradient angle of the road that the car travels over.
        
        """
        # energy = (1/3600) * distance * ((self.mass * gravity * self.rolling_resistance) +
        #                 (0.0386 * air_density * self.drag_coefficient * self.cross_area * velocity ** 2) + # 0.0386 for km/h
        #                 (self.mass * acceleration))
        energy = (1/3600) * distance * (self.rolling_resist() + 
                                        self.hill_climb(velocity, angle) + 
                                        self.air_drag(velocity))
        return energy

    # rolling resistance
    def rolling_resist(self):
        power = self.mass * gravity * self.rolling_resistance
        return power

    # hill climb = Power due to climb = W*V*sin(inclination);
    def hill_climb(self, velocity, angle):
        """
        Calculates how much power is needed to climb up a slope depending on the 
        current velocity and the gradient angle of the road.

        power = mass * gravity * velocity * sin(angle)
        
        Args:
            velocity: The desired speed the car should travel at.
            angle: The gradient angle of the road that the car travels over.
        
        """
        power = self.mass * gravity * velocity * math.sin(angle) # watts
        return power / 1000 # kW
    
    # air drag = P = 0.5*rho*Cd*A*V^3
    def air_drag(self, velocity):
        """
        Calculates how much power is needed to overcome air drag based on the 
        current velocity of the car.

        power = 0.0386 * air density * drag coefficient * cross sectional area * velocity^3
        
        Args:
            velocity: The desired speed the car should travel at.
        
        """
        air_density = 1.225 # kg/m^3
        # convert velocity to m/s and swap constant to 0.5
        power = 0.0386 * air_density * self.drag_c * self.cross_area * velocity**3 # watts
        return power / 1000 # kW
