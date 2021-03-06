def on_enter(event_data):
    """ Once inside the slewing state, set the mount slewing. """
    pocs = event_data.model
    try:
        pocs.logger.debug("Inside slew state")

        # Start the mount slewing
        pocs.observatory.mount.slew_to_target()

        # Wait until mount is_tracking, then transition to track state
        pocs.say("I'm slewing over to the coordinates to track the target.")

        while not pocs.observatory.mount.is_tracking:
            pocs.logger.debug("Slewing to target")
            pocs.sleep()

        pocs.say("I'm at the target, checking pointing.")
        pocs.next_state = 'pointing'

    except Exception as e:
        pocs.say("Wait a minute, there was a problem slewing. Sending to parking. {}".format(e))
