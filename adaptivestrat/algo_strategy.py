import gamelib
import random
import math
import warnings
from sys import maxsize
import json

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.planner = []
        #C:\\Users\\TheDonut\\Documents\\Berkeley\\terminal\\C1GamesStarterKit\\adaptivestrat\\
        with open("config.json") as f:
            self.planner = json.load(f)
    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, FILTER_COST, ENCRYPTOR_COST, DESTRUCTOR_COST, PING_COST, EMP_COST, SCRAMBLER_COST, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        FILTER_COST = config["unitInformation"][0]["cost1"]
        ENCRYPTOR_COST = config["unitInformation"][1]["cost1"]
        DESTRUCTOR_COST = config["unitInformation"][2]["cost1"]
        PING_COST = config["unitInformation"][3]["cost2"]
        EMP_COST = config["unitInformation"][4]["cost2"]
        SCRAMBLER_COST = config["unitInformation"][5]["cost2"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []




    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(False)  #Comment or remove this line to enable warnings.

        self.my_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def my_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        # If the turn is less than 5, stall with Scramblers and wait to see enemy's base
        self.adaptive_defences(game_state)

    def adaptive_defences(self, game_state):
        n = game_state.turn_number
        upgrades = []
        for i in range(min(len(self.planner), n + 1)):
            d = self.planner[i]['defense']
            for j in d:
                if d[j] != []:
                    locations = d[j]
                    for location in locations:
                        unit = game_state.contains_stationary_unit(location)
                        if unit:
                            upgrades.append((j, location))
                        else:
                            if j == 'DESTRUCTOR':
                                game_state.attempt_spawn(DESTRUCTOR, location)
                            if j == 'FILTER':
                                game_state.attempt_spawn(FILTER, location)
                            if j == 'ENCRYPTOR':
                                game_state.attempt_spawn(ENCRYPTOR, location)
        if random.random() < 0.5 and n > 10:
            for upgrade in upgrades:
                location = upgrade[1]
                type = upgrade[0]
                if type == 'FILTER':
                    if random.random() < 0.25:
                        game_state.attempt_remove(location)
                        game_state.attempt_spawn(DESTRUCTOR, location)
                game_state.attempt_upgrade(location)
        a = self.planner[min(len(self.planner) - 1, n)]['attack']
        if random.random() <= 1.0:
            for j in a:
                if j == 'PING':
                    x = PING
                if j == 'EMP':
                    x = EMP
                if j == 'SCRAMBLER':
                    x = SCRAMBLER
                places = a[j][1][1] if len(a[j]) > 1 else 1
                bits = game_state.get_resource(BITS)
                re = (bits - bits % (places * game_state.type_cost(x)[BITS])) / (places * game_state.type_cost(x)[BITS])
                rem =  re if len(a[j]) > 1 and a[j][1][0] == "max" else a[j][1][0]
                if int(rem) > 0:
                    for location in a[j][0]:
                        game_state.attempt_remove(location)
                        path = game_state.find_path_to_edge(location)
                        free = False
                        for li in game_state.game_map.get_edges():
                            if li and path and path[-1] in li:
                                free = True
                        if not free and path and path[-1]:
                            game_state.attempt_remove([path[-1][0], path[-1][1] + 1])
                            game_state.attempt_remove([path[-1][0] - 1, path[-1][1] + 1])
                        game_state.attempt_spawn(x, location, int(rem))


    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        turn = game_state.turn_number
        # Remove locations that are blocked by our own firewalls
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        count = (turn//5) + 1
        # While we have remaining bits to spend lets send out scramblers randomly.
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and len(deploy_locations) > 0 and count > 0:
            count -= 1
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            """
            We don't have to remove the location since multiple information
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        # for x in range(27, 5, -1):
        #     game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        if self.BITS >= 4 * gamelib.GameUnit(EMP, game_state.config).cost[game_state.BITS]:
            game_state.attempt_spawn(EMP, [24, 10], 4)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        damages = events["damage"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))
        # for damage in damages:
            # self.stored_on_locations.append((damage[0], damage[3]))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
