import cv2
from backend.core.config import settings
from backend.core.detector import Detector
from backend.core.distancing import DistanceChecker, AlarmStateMachine, Annotator

def run_test():
    detector = Detector()
    checker = DistanceChecker()
    alarm = AlarmStateMachine()
    annotator = Annotator()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)

    frame_count = 0
    print("Starting Phase 2 Visual Test. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame_count += 1
        
        # Core pipeline
        tracked = detector.process_frame_with_ids(frame)
        result = checker.check_frame(tracked)
        alarm_state = alarm.update(result["violation_count"])
        
        # We explicitly supply 'tracked' to populate the boxes, since DistanceChecker alone does not wrap them in 'result'.
        annotated = annotator.annotate(frame, result, alarm_state, tracked=tracked)

        cv2.imshow("Phase 2 Test", annotated)

        if frame_count % 30 == 0:
            print(f"Frame {frame_count} | People: {result['total_people']} | Violations: {result['violation_count']} | State: {alarm_state['state']}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"Session summary — Total violation events logged: {alarm.total_violations}")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()
