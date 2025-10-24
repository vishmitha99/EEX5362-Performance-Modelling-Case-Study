import random
import statistics

# --- 1. CONFIGURATION PARAMETERS ---
SIMULATION_TIME = 3600 # seconds (1 hour)
VEHICLE_CLEARANCE_TIME = 1.8 # seconds per vehicle (t_clear)
LIGHT_CHANGE_TIME = 5 # seconds (Yellow/All-Red)

# Adaptive Control Parameters (Used in Scenarios 2 & 3)
MIN_GREEN = 15
MAX_GREEN = 50

# --- 2. TRAFFIC LIGHT SIMULATOR CLASS ---

class TrafficLightSimulator:
    def __init__(self, main_arrival_rate, side_arrival_rate, controller_type):
        # Simulation State
        self.time = 0.0
        # Queues store (arrival_time, wait_start_time)
        self.queues = {'main': [], 'side': []} 
        self.current_light = 'main' # 'main' or 'side'
        self.last_green_end_time = 0.0 # Tracks the time a green light ended
        
        # Traffic Parameters (lambda in veh/sec)
        self.lambda_main = main_arrival_rate
        self.lambda_side = side_arrival_rate
        
        # Controller Type & Initial State
        self.controller_type = controller_type
        self.events = [] # Event Queue: (time, type, data)
        self.metrics = {'total_delay': 0, 'vehicles_processed': 0}
        self.queue_data = [] # Stores (time, main_queue_len, side_queue_len)

        # Initial Events
        random.seed(42) # Ensure internal consistency for arrival timing
        self._schedule_arrival('main')
        self._schedule_arrival('side')
        
        # Initial Light Phase (Main Street Green)
        initial_green = 40 if controller_type == 'Fixed' else MAX_GREEN
        self._schedule_event(0.0, 'green_start', 'main')
        self._schedule_event(initial_green, 'yellow_start', 'main')

    # Helper function to schedule events
    def _schedule_event(self, time, type, data=None):
        if time < SIMULATION_TIME:
            self.events.append((time, type, data))
            self.events.sort(key=lambda x: x[0])

    # Schedules the next vehicle arrival for a given street
    def _schedule_arrival(self, street):
        rate = self.lambda_main if street == 'main' else self.lambda_side
        if rate > 0:
            inter_arrival_time = random.expovariate(rate)
            new_time = self.time + inter_arrival_time
            self._schedule_event(new_time, 'arrival', street)

    # Calculates the dynamic green time for the waiting queue
    def _calculate_adaptive_green_time(self, waiting_street):
        queue_len = len(self.queues[waiting_street])
        
        # Time required to clear the current queue, plus a 5 second buffer for safety/reaction time
        required_time = queue_len * VEHICLE_CLEARANCE_TIME + 5 
        
        # Apply min/max constraints
        new_green_time = max(MIN_GREEN, min(MAX_GREEN, required_time))
        return new_green_time

    # Processes all vehicles that can clear the intersection during the green phase duration
    def _process_vehicles(self, street, green_duration):
        cleared_count = 0
        
        # Calculate the maximum number of vehicles that can clear during the green phase
        max_to_clear = int(green_duration / VEHICLE_CLEARANCE_TIME)
        
        for i in range(max_to_clear):
            if self.queues[street]:
                arrival_time, wait_start_time = self.queues[street].pop(0)
                
                # Time the vehicle crosses the stop line
                crossing_time = self.time + i * VEHICLE_CLEARANCE_TIME 
                
                # The total time in the system is crossing_time - arrival_time
                delay = crossing_time - arrival_time
                
                self.metrics['total_delay'] += delay
                self.metrics['vehicles_processed'] += 1
                cleared_count += 1
            else:
                # Queue is empty
                break
        
        # Log the service
        # print(f"Time {self.time:.2f}: {street} GREEN for {green_duration:.2f}s. Cleared {cleared_count} vehicles.")

    # Process a single event
    def _handle_event(self, event):
        self.time, event_type, data = event

        # Log queue status just before event execution
        self.queue_data.append((self.time, len(self.queues['main']), len(self.queues['side'])))
        
        if event_type == 'arrival':
            street = data
            # New vehicle starts waiting (arrival_time, wait_start_time)
            self.queues[street].append((self.time, self.time)) 
            self._schedule_arrival(street)

        elif event_type == 'yellow_start':
            # This is the end of the green light for the current street (data)
            self.last_green_end_time = self.time
            green_street = data
            waiting_street = 'side' if green_street == 'main' else 'main'
            
            # 1. Process vehicles for the phase that just ended
            # The green duration is the time between the last green_start and this event time
            # We must find the last green_start time for this street in the event history
            
            # Since the logic for getting the exact green duration from history is complex in a simple array queue,
            # we rely on the scheduled event duration, which simplifies the model.
            
            # Find the duration of the green phase that *just ended* by checking the difference 
            # between yellow_start time and the green_start time (which is the light change time ago)
            green_duration = self.time - (self.last_green_end_time - LIGHT_CHANGE_TIME) # Simplified assumption, but works for the scheduled light change
            
            # Schedule the start of the next phase (after LIGHT_CHANGE_TIME)
            next_green_start = self.time + LIGHT_CHANGE_TIME 
            self._schedule_event(next_green_start, 'green_start', waiting_street)
            
        elif event_type == 'green_start':
            # Light for the new street (data) is turning green (after All-Red)
            self.current_light = data
            
            # Calculate the green duration for the NEW phase
            if self.controller_type == 'Fixed':
                green_time = 40 if self.current_light == 'main' else 20
            elif self.controller_type == 'Adaptive':
                green_time = self._calculate_adaptive_green_time(self.current_light)
                
            # Now, schedule the yellow start for this phase (i.e., when the green light ends)
            self._schedule_event(self.time + green_time, 'yellow_start', self.current_light)
            
            # Process vehicles for this new green phase
            # The service time is the green_time duration
            self._process_vehicles(self.current_light, green_time)
            
            # For remaining vehicles, their wait_start_time must be updated to the time
            # the red light turns on (which is self.time + green_time)
            red_start_time = self.time + green_time
            for street in ['main', 'side']:
                 for i in range(len(self.queues[street])):
                    arrival_time, _ = self.queues[street][i]
                    self.queues[street][i] = (arrival_time, self.time) # Wait start time is reset to current time

    # Run the simulation loop
    def run_simulation(self):
        
        while self.events and self.events[0][0] < SIMULATION_TIME:
            event = self.events.pop(0)
            self._handle_event(event)

        # Final calculations
        avg_delay = self.metrics['total_delay'] / self.metrics['vehicles_processed'] if self.metrics['vehicles_processed'] > 0 else 0
        throughput = self.metrics['vehicles_processed']
        
        # Calculate Average Queue Length (time-weighted average)
        total_time_weighted_queue_main = 0
        total_time_weighted_queue_side = 0
        
        # Add the final state up to SIMULATION_TIME
        self.queue_data.append((SIMULATION_TIME, len(self.queues['main']), len(self.queues['side'])))

        for i in range(1, len(self.queue_data)):
            # time_delta is the duration between the last event and the current event
            time_delta = self.queue_data[i][0] - self.queue_data[i-1][0]
            if time_delta > 0:
                # queue_length is the length during that time interval
                main_q = self.queue_data[i-1][1]
                side_q = self.queue_data[i-1][2]
                
                total_time_weighted_queue_main += main_q * time_delta
                total_time_weighted_queue_side += side_q * time_delta
            
        avg_queue_main = total_time_weighted_queue_main / SIMULATION_TIME
        avg_queue_side = total_time_weighted_queue_side / SIMULATION_TIME
        avg_queue_total = (avg_queue_main + avg_queue_side) / 2
        
        return avg_delay, avg_queue_total, throughput

# --- 3. EXPERIMENT EXECUTION ---

# Scenario Parameters
scenarios = {
    'S1_Fixed': {
        'main_rate': 0.5, 'side_rate': 0.3, 'controller': 'Fixed',
        'desc': 'Baseline (62.5% Main) with Fixed Timing (40s/20s)'
    },
    'S2_Adaptive': {
        'main_rate': 0.5, 'side_rate': 0.3, 'controller': 'Adaptive',
        'desc': 'Balanced Load with Demand-Responsive (Smart) Timing'
    },
    'S3_Imbalanced': {
        'main_rate': 0.64, 'side_rate': 0.16, 'controller': 'Adaptive', 
        'desc': 'Imbalanced Load (80% Main) with Demand-Responsive Timing'
    }
}

final_results = {}
random.seed(42) # Ensure reproducibility

print("--- Running Traffic Light Simulation Experiments ---")

for name, params in scenarios.items():
    sim = TrafficLightSimulator(params['main_rate'], params['side_rate'], params['controller'])
    avg_delay, avg_queue_total, throughput = sim.run_simulation()
    final_results[name] = {
        'description': params['desc'],
        'delay': round(avg_delay, 2),
        'queue': round(avg_queue_total, 2),
        'throughput': throughput
    }
    
# --- 4. SAMPLE OUTPUT ---
print("\n--- Sample Simulation Output (Key Metrics) ---")
for name, res in final_results.items():
    print(f"\nScenario: {name} - {res['description']}")
    print(f"  Average Vehicle Delay: {res['delay']} seconds")
    print(f"  Average Queue Length: {res['queue']} vehicles")
    print(f"  Total Throughput (1 hr): {res['throughput']} vehicles")