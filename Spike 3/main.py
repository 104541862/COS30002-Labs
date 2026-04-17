import heapq

VERBOSE = True

# Simple node class
class Node:
    def __init__(self, state, parent=None, action=None, g_cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g_cost = g_cost

    def __lt__(self, other):
        return self.g_cost < other.g_cost

def world_satisfies_state(world, state):
    print(f"World, state: {world}, {state}")
    return all(world.get(k) == v for k, v in state.items())

def action_provides_effect(action, state):
    return any(
        key in action["effects"] and action["effects"][key] == value
        for key, value in state.items()
    )

def regress_state(state, action):
    new_state = state.copy()

    # Remove effects satisfied by action
    for key, value in action["effects"].items():
        if key in new_state and new_state[key] == value:
            del new_state[key]

    # Add preconditions
    for key, value in action["preconditions"].items():
        new_state[key] = value

    return new_state


def calculate_heuristic(state, world):
    heuristic = sum(1 for k, v in state.items() if world.get(k) != v)
    print(f"Heuristic: {heuristic}")
    return heuristic


def reconstruct_plan(node):
    plan = []
    while node.parent is not None:
        plan.append(node.action["name"])
        node = node.parent
    return list(reversed(plan))


def state_to_tuple(state):
    return tuple(sorted(state.items()))


# Goal Oriented Action Planner
def generate_goap_plan(current_world_state, desired_goal_state, available_actions):
    open_list = []
    closed_list = set()

    start_node = Node(state=desired_goal_state, parent=None, action=None, g_cost=0)
    start_h = calculate_heuristic(desired_goal_state, current_world_state)

    heapq.heappush(open_list, (start_h, start_node))

    while open_list:
        _, current_node = heapq.heappop(open_list)

        if VERBOSE:
            print(f"Checking node: {current_node.state}")

        # Success
        if world_satisfies_state(current_world_state, current_node.state):
            if VERBOSE:
                print("Plan found!")
            return reconstruct_plan(current_node)

        closed_list.add(state_to_tuple(current_node.state))

        # Expand neighbours
        for action in available_actions:
            if action_provides_effect(action, current_node.state):

                previous_state = regress_state(current_node.state, action)
                state_key = state_to_tuple(previous_state)

                if state_key in closed_list:
                    continue

                new_g_cost = current_node.g_cost + action["cost"]
                h_cost = calculate_heuristic(previous_state, current_world_state)

                if VERBOSE:
                    print(f"  Using action: {action['name']}")
                    print(f"    -> New state: {previous_state}")

                neighbour = Node(
                    state=previous_state,
                    parent=current_node,
                    action=action,
                    g_cost=new_g_cost
                )

                heapq.heappush(open_list, (new_g_cost + h_cost, neighbour))

    if VERBOSE:
        print("No plan found.")

    return None


# Some actual usage
if __name__ == "__main__":

    actions = [
        {
            "name": "FindFood",
            "preconditions": {"hasFood": False},
            "effects": {"hasFood": True},
            "cost": 2
        },
        {
            "name": "Eat",
            "preconditions": {"hasFood": True},
            "effects": {"isHungry": False},
            "cost": 1
        },
        {
            "name": "Sleep",
            "preconditions": {},
            "effects": {"isTired": False},
            "cost": 2
        }
    ]

    world = {
        "hasFood": False,
        "isHungry": True,
        "isTired": True
    }

    goal = {
        "isHungry": False
    }

    plan = generate_goap_plan(world, goal, actions)

    print("\nFinal Plan:", plan)