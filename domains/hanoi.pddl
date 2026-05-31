(define (domain hanoi)
  (:requirements :strips :typing)

  (:types
    disk peg - object
  )

  (:predicates
    (on ?d - disk ?p - peg)
    (on-table ?d - disk)
    (clear ?d - disk)
    (clear-peg ?p - peg)
    (smaller ?d1 - disk ?d2 - disk)
    (on-disk ?d1 - disk ?d2 - disk)
  )

  (:action move-disk
    :parameters (?d - disk ?from - peg ?to - peg)
    :precondition (and
      (on ?d ?from)
      (clear ?d)
      (clear-peg ?to)
    )
    :effect (and
      (on ?d ?to)
      (clear-peg ?from)
      (not (on ?d ?from))
      (not (clear-peg ?to))
    )
  )
)
