(define (domain tyreworld)
  (:requirements :strips :typing)

  (:types
    obj - object
  )

  (:predicates
    (in ?x - obj ?y - obj)
    (intact ?x - obj)
    (inflated ?x - obj)
    (fastened ?x - obj)
    (unfastened ?x - obj)
    (have ?x - obj)
    (free ?x - obj)
    (on-ground ?x - obj)
    (not-on-ground ?x - obj)
    (tight ?x - obj ?y - obj)
    (loose ?x - obj ?y - obj)
    (jacked-up ?x - obj)
    (open ?x - obj)
    (closed ?x - obj)
    (is-wheel ?x - obj)
    (is-nut ?x - obj)
    (is-pump ?x - obj)
    (is-boot ?x - obj)
    (is-hub ?x - obj)
    (is-wrench ?x - obj)
    (is-jack ?x - obj)
  )

  (:action open-container
    :parameters (?x - obj)
    :precondition (and (closed ?x) (have ?x))
    :effect (and
      (open ?x)
      (not (closed ?x))
    )
  )

  (:action close-container
    :parameters (?x - obj)
    :precondition (open ?x)
    :effect (and
      (closed ?x)
      (not (open ?x))
    )
  )

  (:action fetch
    :parameters (?x - obj ?y - obj)
    :precondition (and (in ?x ?y) (open ?y))
    :effect (and
      (have ?x)
      (not (in ?x ?y))
    )
  )

  (:action put-away
    :parameters (?x - obj ?y - obj)
    :precondition (and (have ?x) (open ?y))
    :effect (and
      (in ?x ?y)
      (not (have ?x))
    )
  )

  (:action loosen
    :parameters (?x - obj ?y - obj)
    :precondition (and
      (is-nut ?x)
      (is-hub ?y)
      (have ?x)
      (tight ?x ?y)
      (on-ground ?y)
    )
    :effect (and
      (loose ?x ?y)
      (not (tight ?x ?y))
    )
  )

  (:action tighten
    :parameters (?x - obj ?y - obj)
    :precondition (and
      (is-nut ?x)
      (is-hub ?y)
      (have ?x)
      (loose ?x ?y)
      (on-ground ?y)
    )
    :effect (and
      (tight ?x ?y)
      (not (loose ?x ?y))
    )
  )

  (:action jack-up
    :parameters (?y - obj ?j - obj)
    :precondition (and
      (is-hub ?y)
      (is-jack ?j)
      (on-ground ?y)
      (have ?j)
    )
    :effect (and
      (jacked-up ?y)
      (not-on-ground ?y)
      (not (on-ground ?y))
    )
  )

  (:action jack-down
    :parameters (?y - obj ?j - obj)
    :precondition (and
      (is-hub ?y)
      (is-jack ?j)
      (jacked-up ?y)
      (have ?j)
    )
    :effect (and
      (on-ground ?y)
      (not (jacked-up ?y))
      (not (not-on-ground ?y))
    )
  )

  (:action undo
    :parameters (?x - obj ?y - obj)
    :precondition (and
      (is-nut ?x)
      (is-hub ?y)
      (jacked-up ?y)
      (have ?x)
      (loose ?x ?y)
      (fastened ?y)
    )
    :effect (and
      (unfastened ?y)
      (free ?y)
      (not (fastened ?y))
      (not (loose ?x ?y))
    )
  )

  (:action do-up
    :parameters (?x - obj ?y - obj)
    :precondition (and
      (is-nut ?x)
      (is-hub ?y)
      (jacked-up ?y)
      (have ?x)
      (unfastened ?y)
      (free ?y)
    )
    :effect (and
      (loose ?x ?y)
      (fastened ?y)
      (not (unfastened ?y))
      (not (free ?y))
    )
  )

  (:action remove-wheel
    :parameters (?w - obj ?y - obj)
    :precondition (and
      (is-wheel ?w)
      (is-hub ?y)
      (jacked-up ?y)
      (on-ground ?w)
      (unfastened ?y)
    )
    :effect (and
      (have ?w)
      (free ?y)
      (not (on-ground ?w))
    )
  )

  (:action put-on-wheel
    :parameters (?w - obj ?y - obj)
    :precondition (and
      (is-wheel ?w)
      (is-hub ?y)
      (jacked-up ?y)
      (have ?w)
      (free ?y)
      (unfastened ?y)
    )
    :effect (and
      (on-ground ?w)
      (not (have ?w))
      (not (free ?y))
    )
  )

  (:action inflate
    :parameters (?w - obj ?p - obj)
    :precondition (and
      (is-wheel ?w)
      (is-pump ?p)
      (have ?p)
      (intact ?w)
      (not-on-ground ?w)
    )
    :effect (inflated ?w)
  )
)
