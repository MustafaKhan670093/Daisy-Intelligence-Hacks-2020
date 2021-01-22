import random
from random import randrange
import numpy as np
from typing import List, Dict, Optional, Tuple
import copy

count = 0
from site_location import SiteLocationPlayer, Store, SiteLocationMap, euclidian_distances, attractiveness_allocation, \
    closest_store_allocation


class RandomPlayer(SiteLocationPlayer):
    """
    Player attempts to place the maximum stores, with each store type and
    position chosen randomly.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        stores = []
        for _ in range(self.config["max_stores_per_round"]):
            store_types = list(self.config["store_config"].keys())
            store = Store((random.randrange(0, slmap.size[0]),
                           random.randrange(0, slmap.size[1])),
                          random.choice(store_types))
            stores.append(store)
        self.stores_to_place = stores


class MaxDensityPlayer(SiteLocationPlayer):
    """ 
    Player always selects the highest density location at least 50 units
    away from the nearest store. 

    Store type will always be the largest one it can afford.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        # Configurable minimum distance away to place store
        min_dist = 50
        # Check if it can buy any store at all
        if current_funds < store_conf['small']['capital_cost']:
            self.stores_to_place = []
            return
        # Choose largest store type possible
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'
        # Find highest population location
        all_stores_pos = []
        for player, player_stores in store_locations.items():
            for player_store in player_stores:
                all_stores_pos.append(player_store.pos)

        sorted_indices = tuple(map(tuple, np.dstack(
            np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))
        for max_pos in sorted_indices:
            too_close = False
            for pos in all_stores_pos:
                dist = np.sqrt(np.square(max_pos[0] - pos[0]) + np.square(max_pos[1] - pos[1]))
                if dist < min_dist:
                    too_close = True
            if not too_close:
                self.stores_to_place = [Store(max_pos, store_type)]
                return


class CopycatPlayer(SiteLocationPlayer):
    """ 
    Player places an identical store at the location of a random opponent's store.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):

        self_stores_pos = []
        for store in store_locations[self.player_id]:
            self_stores_pos.append(store.pos)

        opp_store_locations = {k: v for (k, v) in store_locations.items() if k != self.player_id}
        opp_all_stores = []
        for player, player_stores in opp_store_locations.items():
            for player_store in player_stores:
                if player_store.pos not in self_stores_pos:
                    opp_all_stores.append(player_store)
        if not opp_all_stores:
            self.stores_to_place = []
            return
        else:
            self.stores_to_place = [random.choice(opp_all_stores)]
            return


class AllocSamplePlayer(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function. 
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        num_rand = 100

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x, y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        return


''''
class ControlShiftSolveAgent(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        num_rand = 50

        # Location of all stores (keep outside/seperate because this repeats computations)
        all_stores_pos = []
        for player, player_stores in store_locations.items():
            for player_store in player_stores:
                all_stores_pos.append(player_store.pos)

        # Max population density
        sorted_indices = tuple(map(tuple, np.dstack(
            np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))

        search_center = sorted_indices[random.randint(0, len(sorted_indices))]
        for max_pos in sorted_indices:
            too_close = False
            for pos in all_stores_pos:
                dist = np.sqrt(np.square(max_pos[0] - pos[0]) + np.square(max_pos[1] - pos[1]))
                if dist < 50:
                    too_close = True
            if not too_close:
                search_center = max_pos
                break

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(max(0, search_center[0] - 50), min(slmap.size[0], search_center[0] + 50))
            y = random.randint(max(0, search_center[1] - 50), min(slmap.size[1], search_center[1] + 50))
            sample_pos.append((x, y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        return
        '''


#
# class ControlShiftSolve_SwitchAlgo(SiteLocationPlayer):
#     """
#     For the first iteration, we do a MaxDensity play.
#     Then, agent samples locations and selects the highest allocating one using
#     the allocation function and finally switches
#     to a closest_store_allocation later in the game.
#     """
#     round = 0
#
#     def place_stores(self, slmap: SiteLocationMap,
#                      store_locations: Dict[int, List[Store]],
#                      current_funds: float):
#         print(' ')
#         print('Round:')
#         print(round)
#         print(' ')
#         if round == 0:
#             round += 1
#             store_conf = self.config['store_config']
#             # Configurable minimum distance away to place store
#             min_dist = 50
#             # Check if it can buy any store at all
#             if current_funds < store_conf['small']['capital_cost']:
#                 self.stores_to_place = []
#                 return
#             # Choose largest store type possible
#             if current_funds >= store_conf['large']['capital_cost']:
#                 store_type = 'large'
#             elif current_funds >= store_conf['medium']['capital_cost']:
#                 store_type = 'medium'
#             else:
#                 store_type = 'small'
#             # Find highest population location
#             all_stores_pos = []
#             for player, player_stores in store_locations.items():
#                 for player_store in player_stores:
#                     all_stores_pos.append(player_store.pos)
#
#             sorted_indices = tuple(map(tuple, np.dstack(
#                 np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))
#             for max_pos in sorted_indices:
#                 too_close = False
#                 for pos in all_stores_pos:
#                     dist = np.sqrt(np.square(max_pos[0] - pos[0]) + np.square(max_pos[1] - pos[1]))
#                     if dist < min_dist:
#                         too_close = True
#                 if not too_close:
#                     self.stores_to_place = [Store(max_pos, store_type)]
#                     return
#
#         elif round > 0 and round < 5:
#             round += 1
#             store_conf = self.config['store_config']
#             num_rand = 100
#
#             sample_pos = []
#             for i in range(num_rand):
#                 x = random.randint(0, slmap.size[0])
#                 y = random.randint(0, slmap.size[1])
#                 sample_pos.append((x, y))
#             # Choose largest store type possible:
#             if current_funds >= store_conf['large']['capital_cost']:
#                 store_type = 'large'
#             elif current_funds >= store_conf['medium']['capital_cost']:
#                 store_type = 'medium'
#             else:
#                 store_type = 'small'
#
#             best_score = 0
#             best_pos = []
#             for pos in sample_pos:
#                 sample_store = Store(pos, store_type)
#                 temp_store_locations = copy.deepcopy(store_locations)
#                 temp_store_locations[self.player_id].append(sample_store)
#                 sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
#                 sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
#                 if sample_score > best_score:
#                     best_score = sample_score
#                     best_pos = [pos]
#                 elif sample_score == best_score:
#                     best_pos.append(pos)
#
#             # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
#             # pos = random.choice(max_alloc_positons)
#             self.stores_to_place = [Store(random.choice(best_pos), store_type)]
#             return
#
#         else:
#             round += 1
#             store_conf = self.config['store_config']
#             num_rand = 100
#
#             sample_pos = []
#             for i in range(num_rand):
#                 x = random.randint(0, slmap.size[0])
#                 y = random.randint(0, slmap.size[1])
#                 sample_pos.append((x, y))
#             # Choose largest store type possible:
#             if current_funds >= store_conf['large']['capital_cost']:
#                 store_type = 'large'
#             elif current_funds >= store_conf['medium']['capital_cost']:
#                 store_type = 'medium'
#             else:
#                 store_type = 'small'
#
#             best_score = 0
#             best_pos = []
#             for pos in sample_pos:
#                 sample_store = Store(pos, store_type)
#                 temp_store_locations = copy.deepcopy(store_locations)
#                 temp_store_locations[self.player_id].append(sample_store)
#                 sample_alloc = closest_store_allocation(slmap, temp_store_locations, store_conf)
#                 sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
#                 if sample_score > best_score:
#                     best_score = sample_score
#                     best_pos = [pos]
#                 elif sample_score == best_score:
#                     best_pos.append(pos)
#
#             # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
#             # pos = random.choice(max_alloc_positons)
#             self.stores_to_place = [Store(random.choice(best_pos), store_type)]
#             return


class Shawty(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        global count
        count += 1
        store_conf = self.config['store_config']
        num_rand = 100

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x, y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            if count < 8:
                print(count)
                sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
                sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            else:
                print(count)
                sample_alloc = closest_store_allocation(slmap, temp_store_locations)
                sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        return


class LikeA(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        global count
        count += 1
        store_conf = self.config['store_config']
        num_rand = 100

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x, y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            if count < 9:
                sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
                sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            else:
                sample_alloc = closest_store_allocation(slmap, temp_store_locations, store_conf)
                sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        pos1 = random.choice(best_pos)
        if count <= 8:
            self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        else:
            temp_current_funds = current_funds - store_conf[store_type]['capital_cost']
            print(' ')
            print(temp_current_funds)
            print(' ')
            if temp_current_funds >= store_conf['large']['capital_cost']:
                store_type_2 = 'large'
            elif temp_current_funds >= store_conf['medium']['capital_cost']:
                store_type_2 = 'medium'
            else:
                store_type_2 = 'small'

            pos2 = random.choice(best_pos)
            self.stores_to_place = [Store(pos1, store_type), Store(pos2, store_type_2)]
            return



class Melody(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function.
    """

    def place_stores(self, slmap: SiteLocationMap,
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        global count
        count += 1
        if count <= 3:
            store_conf = self.config['store_config']
            # Configurable minimum distance away to place store
            min_dist = 50
            # Check if it can buy any store at all
            if current_funds < store_conf['small']['capital_cost']:
                self.stores_to_place = []
                return
            # Choose largest store type possible
            if current_funds >= store_conf['large']['capital_cost']:
                store_type = 'large'
            elif current_funds >= store_conf['medium']['capital_cost']:
                store_type = 'medium'
            else:
                store_type = 'small'
            # Find highest population location
            all_stores_pos = []
            for player, player_stores in store_locations.items():
                for player_store in player_stores:
                    all_stores_pos.append(player_store.pos)

            sorted_indices = tuple(map(tuple, np.dstack(
                np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))
            for max_pos in sorted_indices:
                too_close = False
                for pos in all_stores_pos:
                    dist = np.sqrt(np.square(max_pos[0] - pos[0]) + np.square(max_pos[1] - pos[1]))
                    if dist < min_dist:
                        too_close = True
                if not too_close:
                    self.stores_to_place = [Store(max_pos, store_type)]
                    return
        else:
            store_conf = self.config['store_config']
            num_rand = 100

            sample_pos = []
            for i in range(num_rand):
                x = random.randint(0, slmap.size[0])
                y = random.randint(0, slmap.size[1])
                sample_pos.append((x, y))
            # Choose largest store type possible:
            if current_funds >= store_conf['large']['capital_cost']:
                store_type = 'large'
            elif current_funds >= store_conf['medium']['capital_cost']:
                store_type = 'medium'
            else:
                store_type = 'small'

            best_score = 0
            best_pos = []
            for pos in sample_pos:
                sample_store = Store(pos, store_type)
                temp_store_locations = copy.deepcopy(store_locations)
                temp_store_locations[self.player_id].append(sample_store)
                sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
                sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
                if sample_score > best_score:
                    best_score = sample_score
                    best_pos = [pos]
                elif sample_score == best_score:
                    best_pos.append(pos)

            # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
            # pos = random.choice(max_alloc_positons)
            self.stores_to_place = [Store(random.choice(best_pos), store_type)]
            return

        '''
        store_conf = self.config['store_config']
        num_rand = 100

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x, y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        #all stores
        all_stores_pos = []
        for player, player_stores in store_locations.items():
            for player_store in player_stores:
                all_stores_pos.append(player_store.pos)

        #max densities
        sorted_indices = tuple(map(tuple, np.dstack(np.unravel_index(np.argsort(slmap.population_distribution.ravel()), slmap.size))[0][::-1]))

        best_score = 0
        best_pos = []

        #max density starts here
        if count < 3:
          random_value = random.randint(0,len(sorted_indices)-1)
          max_pos = sorted_indices[random_value]
          self.stores_to_place = [Store(max_pos, store_type)]
          return

        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            # else:
            #     print(count)
            #     sample_alloc = closest_store_allocation(slmap, temp_store_locations)
            #     sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
            self.stores_to_place = [Store(random.choice(best_pos), store_type)]
            return
        ''''