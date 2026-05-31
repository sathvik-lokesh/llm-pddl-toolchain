(define (domain logistics)
  (:requirements :strips :typing)

  (:types
    vehicle physobj - object
    package - physobj
    truck airplane - vehicle
    location - object
    airport - location
    city - object
  )

  (:predicates
    (in-city ?loc - location ?c - city)
    (at ?obj - physobj ?loc - location)
    (in ?pkg - package ?veh - vehicle)
  )

  (:action load-truck
    :parameters (?pkg - package ?trk - truck ?loc - location)
    :precondition (and (at ?trk ?loc) (at ?pkg ?loc))
    :effect (and
      (in ?pkg ?trk)
      (not (at ?pkg ?loc))
    )
  )

  (:action unload-truck
    :parameters (?pkg - package ?trk - truck ?loc - location)
    :precondition (and (at ?trk ?loc) (in ?pkg ?trk))
    :effect (and
      (at ?pkg ?loc)
      (not (in ?pkg ?trk))
    )
  )

  (:action load-airplane
    :parameters (?pkg - package ?apn - airplane ?apt - airport)
    :precondition (and (at ?apn ?apt) (at ?pkg ?apt))
    :effect (and
      (in ?pkg ?apn)
      (not (at ?pkg ?apt))
    )
  )

  (:action unload-airplane
    :parameters (?pkg - package ?apn - airplane ?apt - airport)
    :precondition (and (at ?apn ?apt) (in ?pkg ?apn))
    :effect (and
      (at ?pkg ?apt)
      (not (in ?pkg ?apn))
    )
  )

  (:action drive-truck
    :parameters (?trk - truck ?from - location ?to - location ?c - city)
    :precondition (and (at ?trk ?from) (in-city ?from ?c) (in-city ?to ?c))
    :effect (and
      (at ?trk ?to)
      (not (at ?trk ?from))
    )
  )

  (:action fly-airplane
    :parameters (?apn - airplane ?from - airport ?to - airport)
    :precondition (at ?apn ?from)
    :effect (and
      (at ?apn ?to)
      (not (at ?apn ?from))
    )
  )
)
