#! /usr/bin/env python

import rospy

import actionlib
import math
import smarc_msgs.msg
import smarc_bt.msg
from std_msgs.msg import Float64
import tf
from geometry_msgs.msg import Point

class GotoWaypointAction(object):
    # create messages that are used to publish feedback/result
    _feedback = smarc_bt.msg.GotoWaypointFeedback()
    _result = smarc_bt.msg.GotoWaypointResult()

    def __init__(self, name, _tf_listener):
        self.tf_listerner = _tf_listener
        self._action_name = name
        self._as = actionlib.SimpleActionServer(self._action_name, smarc_bt.msg.GotoWaypointAction, execute_cb=self.execute_cb, auto_start = False)
        self._as.start()

        self.waypoint_pub = rospy.Publisher("ctrl/waypoint_setpoint_utm", Point, queue_size=1)
        self.rpm_pub = rospy.Publisher("ctrl/rpm_setpoint", smarc_msgs.msg.ThrusterRPM, queue_size=1)
        self.speed_pub = rospy.Publisher("ctrl/speed_setpoint", Float64, queue_size=1)
        self.depth_pub = rospy.Publisher("ctrl/depth_setpoint", Float64, queue_size=1)
        #TODO:
        # speed
        # altude

    def execute_cb(self, goal):
        # helper variables
        r = rospy.Rate(1)
        success = True

        # publish info to the console for the user
        print("Lolo waypoint actionserver started")

        # start executing the action
        while not rospy.is_shutdown():
            # this step is not necessary, the sequence is computed at 1 Hz for demonstration purposes
            r.sleep()

            # check that preempt has not been requested by the client
            if self._as.is_preempt_requested():
                rospy.loginfo('%s: Preempted' % self._action_name)
                self._as.set_preempted()
                success = False
                break

            try:
                (trans,rot) = listener.lookupTransform('utm', '/lolo/base_link', rospy.Time(0))
                print("lolo position: " + str(trans))
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                print("tranform error")
                self._as.set_preempted()
                success = False
                break;

            #print(goal)
            #Calculate the distance to target
            dx = goal.waypoint.pose.pose.position.x - trans[0]
            dy = goal.waypoint.pose.pose.position.y - trans[1]
            dist = math.sqrt(dx*dx + dy*dy)
            print("dx : " + str(dx))
            print("dy : " + str(dy))
            print("distance to target: " + str(dist))


            # publish feedback
            self._feedback.ETA = rospy.get_rostime() + rospy.Duration((dist / 0.6)) #TOTO change 0.6 for actual speed
            self._as.publish_feedback(self._feedback)

            #Check if distance to goal < tolerance
            if(dist < goal.waypoint.goal_tolerance):
                print("Goal reached")
                break; #Goal reached


            print("Send setpoints to lolo")
            #send setpoints to lolo
            target = goal.waypoint.pose.pose.position
            print("target:")
            print(target)
            self.waypoint_pub.publish(target)

            if(goal.waypoint.z_control_mode == goal.waypoint.Z_CONTROL_DEPTH):
                self.depth_pub.publish(goal.waypoint.travel_depth)
            elif(goal.waypoint.z_control_mode == goal.waypoint.Z_CONTROL_ALTITUDE):
                print("No altitude following yet :)")
                self.depth_pub.publish(-30)
            else:
                print("Depth control mode not set. staying at the surface")
                self.depth_pub.publish(-30)

            if(goal.waypoint.speed_control_mode == goal.waypoint.SPEED_CONTROL_RPM):
                msg = smarc_msgs.msg.ThrusterRPM()
                msg.rpm = int(goal.waypoint.travel_rpm)
                self.rpm_pub.publish(msg)
            elif(goal.waypoint.speed_control_mode == goal.waypoint.SPEED_CONTROL_SPEED):
                self.speed_pub.publish(goal.waypoint.travel_speed)
            else:
                msg = smarc_msgs.msg.ThrusterRPM()
                msg.rpm = int(goal.waypoint.travel_rpm)
                self.rpm_pub.publish(msg)


        print("Send 0 rpm to lolo") #TODO remove this once the timeout is implemented on lolo
        #self.waypoint_pub.publish(target)
        self.depth_pub.publish(-30)
        msg = smarc_msgs.msg.ThrusterRPM()
        self.rpm_pub.publish(msg)

        if success:
            self._result.reached_waypoint = True
            rospy.loginfo('%s: Waypoint reached' % self._action_name)
            self._as.set_succeeded(self._result)


if __name__ == '__main__':
    rospy.init_node('lolo_waypoint_action')
    listener = tf.TransformListener()
    server = GotoWaypointAction("ctrl/goto_waypoint", listener)
    rospy.spin()
