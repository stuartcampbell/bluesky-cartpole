import pprint

from bluesky.tests.utils import DocCollector as DocumentCollector

from bluesky_adaptive.per_event import (
    recommender_factory,
    adaptive_plan,
)

from bluesky_cartpole.cartpole import CartPole, CartpoleRecommender, get_cartpole_agent


def test_cartpole_device():
    cartpole = CartPole()

    description = cartpole.describe()
    pprint.pprint(description)

    cartpole.stage()

    cartpole.trigger()
    pprint.pprint(cartpole)

    cartpole_state = cartpole.read()
    pprint.pprint(cartpole_state)


def test_per_event_adaptive_plan(RE):

    cartpole = CartPole(max_episode_timesteps=10)
    cartpole_agent = get_cartpole_agent(cartpole=cartpole)
    cartpole_recommender = CartpoleRecommender(cartpole_agent=cartpole_agent)
    to_recommender, from_recommender = recommender_factory(
        cartpole_recommender,
        independent_keys=[cartpole.action.name],
        # recommender expects the dependent values in this order
        dependent_keys=[
            cartpole.next_state.name,
            cartpole.reward.name,
            cartpole.terminal.name,
            cartpole.state_after_reset.name,
        ],
    )

    action = cartpole_agent.act(states=cartpole.state_after_reset.get())

    RE(
        adaptive_plan(
            dets=[cartpole],
            first_point={cartpole.action: action},
            to_brains=to_recommender,
            from_brains=from_recommender,
        )
    )

    #pprint.pprint(f"cartpole_agent.get_variables(): {cartpole_agent.get_variables()}")


def __test_cartpole_recommender(RE, hw):

    recommender = CartpoleRecommender()

    cb, queue = recommender_factory(recommender, ["motor"], ["det"])
    dc = DocumentCollector()

    RE.subscribe(dc.insert)
    RE(adaptive_plan([hw.det], {hw.motor: 0}, to_brains=cb, from_brains=queue))

    assert len(dc.start) == 1
    assert len(dc.event) == 1
    (events,) = dc.event.values()
    assert len(events) == 4
