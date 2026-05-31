(define (domain freecell)
  (:requirements :strips :typing)

  (:types
    card suit num cols - object
  )

  (:predicates
    (on ?c1 - card ?c2 - card)
    (incol ?c - card ?col - cols)
    (home ?c - card)
    (bottomcol ?c - card)
    (colspace ?col - cols)
    (freecel ?c - card)
    (clear ?c - card)
    (successor ?n1 - num ?n2 - num)
    (canstack ?c1 - card ?c2 - card)
    (suit ?c - card ?s - suit)
    (value ?c - card ?n - num)
    (homesuit ?s - suit ?n - num)
  )

  (:action move-card-to-freecell
    :parameters (?c - card ?col - cols)
    :precondition (and
      (incol ?c ?col)
      (clear ?c)
    )
    :effect (and
      (freecel ?c)
      (not (incol ?c ?col))
    )
  )

  (:action move-card-from-freecell
    :parameters (?c - card ?c2 - card ?col - cols)
    :precondition (and
      (freecel ?c)
      (incol ?c2 ?col)
      (clear ?c2)
      (canstack ?c ?c2)
    )
    :effect (and
      (incol ?c ?col)
      (on ?c ?c2)
      (not (freecel ?c))
      (not (clear ?c2))
    )
  )

  (:action move-card-to-column
    :parameters (?c - card ?c2 - card ?col1 - cols ?col2 - cols)
    :precondition (and
      (incol ?c ?col1)
      (clear ?c)
      (incol ?c2 ?col2)
      (clear ?c2)
      (canstack ?c ?c2)
    )
    :effect (and
      (incol ?c ?col2)
      (on ?c ?c2)
      (not (incol ?c ?col1))
      (not (clear ?c2))
    )
  )

  (:action move-card-to-home
    :parameters (?c - card ?col - cols ?s - suit ?n - num ?np - num)
    :precondition (and
      (incol ?c ?col)
      (clear ?c)
      (suit ?c ?s)
      (value ?c ?n)
      (homesuit ?s ?np)
      (successor ?n ?np)
    )
    :effect (and
      (home ?c)
      (homesuit ?s ?n)
      (not (incol ?c ?col))
      (not (homesuit ?s ?np))
    )
  )
)
