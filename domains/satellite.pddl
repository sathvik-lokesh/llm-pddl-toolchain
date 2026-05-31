(define (domain satellite)
  (:requirements :strips :typing)

  (:types
    satellite direction instrument mode - object
  )

  (:predicates
    (on-board ?i - instrument ?s - satellite)
    (supports ?i - instrument ?m - mode)
    (pointing ?s - satellite ?d - direction)
    (power-avail ?s - satellite)
    (power-on ?i - instrument)
    (calibrated ?i - instrument)
    (have-image ?d - direction ?m - mode)
    (calibration-target ?i - instrument ?d - direction)
  )

  (:action turn-to
    :parameters (?s - satellite ?new-d - direction ?prev-d - direction)
    :precondition (pointing ?s ?prev-d)
    :effect (and
      (pointing ?s ?new-d)
      (not (pointing ?s ?prev-d))
    )
  )

  (:action switch-on
    :parameters (?i - instrument ?s - satellite)
    :precondition (and (on-board ?i ?s) (power-avail ?s))
    :effect (and
      (power-on ?i)
      (not (calibrated ?i))
      (not (power-avail ?s))
    )
  )

  (:action switch-off
    :parameters (?i - instrument ?s - satellite)
    :precondition (and (on-board ?i ?s) (power-on ?i))
    :effect (and
      (power-avail ?s)
      (not (power-on ?i))
    )
  )

  (:action calibrate
    :parameters (?s - satellite ?i - instrument ?d - direction)
    :precondition (and
      (on-board ?i ?s)
      (calibration-target ?i ?d)
      (pointing ?s ?d)
      (power-on ?i)
    )
    :effect (calibrated ?i)
  )

  (:action take-image
    :parameters (?s - satellite ?d - direction ?i - instrument ?m - mode)
    :precondition (and
      (calibrated ?i)
      (on-board ?i ?s)
      (supports ?i ?m)
      (power-on ?i)
      (pointing ?s ?d)
    )
    :effect (have-image ?d ?m)
  )
)
