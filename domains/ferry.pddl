(define (domain ferry)
  (:requirements :strips :typing)

  (:types
    car location - object
  )

  (:predicates
    (at ?c - car ?l - location)
    (on ?c - car)
    (empty-ferry)
    (ferry-at ?l - location)
  )

  (:action board
    :parameters (?c - car ?l - location)
    :precondition (and (at ?c ?l) (ferry-at ?l) (empty-ferry))
    :effect (and
      (on ?c)
      (not (at ?c ?l))
      (not (empty-ferry))
    )
  )

  (:action sail
    :parameters (?from - location ?to - location)
    :precondition (ferry-at ?from)
    :effect (and
      (ferry-at ?to)
      (not (ferry-at ?from))
    )
  )

  (:action debark
    :parameters (?c - car ?l - location)
    :precondition (and (on ?c) (ferry-at ?l))
    :effect (and
      (at ?c ?l)
      (empty-ferry)
      (not (on ?c))
    )
  )
)
