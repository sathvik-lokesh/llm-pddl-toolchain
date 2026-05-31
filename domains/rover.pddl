(define (domain rover)
  (:requirements :strips :typing)

  (:types
    rover waypoint store camera mode lander objective - object
  )

  (:predicates
    (at ?r - rover ?w - waypoint)
    (at-lander ?l - lander ?w - waypoint)
    (can-traverse ?r - rover ?from - waypoint ?to - waypoint)
    (equipped-for-soil-analysis ?r - rover)
    (equipped-for-rock-analysis ?r - rover)
    (equipped-for-imaging ?r - rover)
    (empty ?s - store)
    (have-rock-analysis ?r - rover ?w - waypoint)
    (have-soil-analysis ?r - rover ?w - waypoint)
    (full ?s - store)
    (calibrated ?c - camera ?r - rover)
    (supports ?c - camera ?m - mode)
    (available ?r - rover)
    (visible ?w1 - waypoint ?w2 - waypoint)
    (have-image ?r - rover ?o - objective ?m - mode)
    (communicated-soil-data ?w - waypoint)
    (communicated-rock-data ?w - waypoint)
    (communicated-image-data ?o - objective ?m - mode)
    (at-soil-sample ?w - waypoint)
    (at-rock-sample ?w - waypoint)
    (visible-from ?o - objective ?w - waypoint)
    (store-of ?s - store ?r - rover)
    (calibration-target ?c - camera ?o - objective)
    (on-board ?c - camera ?r - rover)
    (channel-free ?l - lander)
    (in-sun ?w - waypoint)
  )

  (:action navigate
    :parameters (?r - rover ?from - waypoint ?to - waypoint)
    :precondition (and
      (can-traverse ?r ?from ?to)
      (available ?r)
      (at ?r ?from)
    )
    :effect (and
      (at ?r ?to)
      (not (at ?r ?from))
    )
  )

  (:action sample-soil
    :parameters (?r - rover ?s - store ?w - waypoint)
    :precondition (and
      (at ?r ?w)
      (at-soil-sample ?w)
      (equipped-for-soil-analysis ?r)
      (store-of ?s ?r)
      (empty ?s)
    )
    :effect (and
      (have-soil-analysis ?r ?w)
      (full ?s)
      (not (empty ?s))
      (not (at-soil-sample ?w))
    )
  )

  (:action sample-rock
    :parameters (?r - rover ?s - store ?w - waypoint)
    :precondition (and
      (at ?r ?w)
      (at-rock-sample ?w)
      (equipped-for-rock-analysis ?r)
      (store-of ?s ?r)
      (empty ?s)
    )
    :effect (and
      (have-rock-analysis ?r ?w)
      (full ?s)
      (not (empty ?s))
      (not (at-rock-sample ?w))
    )
  )

  (:action drop
    :parameters (?r - rover ?s - store)
    :precondition (and (store-of ?s ?r) (full ?s))
    :effect (and
      (empty ?s)
      (not (full ?s))
    )
  )

  (:action calibrate
    :parameters (?r - rover ?c - camera ?o - objective ?w - waypoint)
    :precondition (and
      (equipped-for-imaging ?r)
      (calibration-target ?c ?o)
      (at ?r ?w)
      (visible-from ?o ?w)
      (on-board ?c ?r)
    )
    :effect (calibrated ?c ?r)
  )

  (:action take-image
    :parameters (?r - rover ?w - waypoint ?o - objective ?c - camera ?m - mode)
    :precondition (and
      (calibrated ?c ?r)
      (on-board ?c ?r)
      (equipped-for-imaging ?r)
      (supports ?c ?m)
      (visible-from ?o ?w)
      (at ?r ?w)
    )
    :effect (and
      (have-image ?r ?o ?m)
      (not (calibrated ?c ?r))
    )
  )

  (:action communicate-soil-data
    :parameters (?r - rover ?l - lander ?w - waypoint ?wl - waypoint)
    :precondition (and
      (at ?r ?w)
      (at-lander ?l ?wl)
      (have-soil-analysis ?r ?w)
      (visible ?w ?wl)
      (available ?r)
      (channel-free ?l)
    )
    :effect (and
      (communicated-soil-data ?w)
      (not (channel-free ?l))
      (channel-free ?l)
    )
  )

  (:action communicate-rock-data
    :parameters (?r - rover ?l - lander ?w - waypoint ?wl - waypoint)
    :precondition (and
      (at ?r ?w)
      (at-lander ?l ?wl)
      (have-rock-analysis ?r ?w)
      (visible ?w ?wl)
      (available ?r)
      (channel-free ?l)
    )
    :effect (and
      (communicated-rock-data ?w)
      (not (channel-free ?l))
      (channel-free ?l)
    )
  )

  (:action communicate-image-data
    :parameters (?r - rover ?l - lander ?o - objective ?m - mode ?w - waypoint ?wl - waypoint)
    :precondition (and
      (at ?r ?w)
      (at-lander ?l ?wl)
      (have-image ?r ?o ?m)
      (visible ?w ?wl)
      (available ?r)
      (channel-free ?l)
    )
    :effect (and
      (communicated-image-data ?o ?m)
      (not (channel-free ?l))
      (channel-free ?l)
    )
  )
)
