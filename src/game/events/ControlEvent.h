//
// Created by zr on 23-2-16.
//

#ifndef TANK_TROUBLE_CONTROL_EVENT_H
#define TANK_TROUBLE_CONTROL_EVENT_H
#include "reactor/Event.h"

namespace TankTrouble
{
    class ControlEvent : public ev::Event
    {
    public:
        // Move forward, stop, reverse, turn clockwise, turn counterclockwise.
        enum Operation
        {
            Forward, Backward, RotateCW, RotateCCW, Fire,
            StopForward, StopBackward, StopRotateCW, StopRotateCCW
        };

        explicit ControlEvent(Operation op);
        ControlEvent();
        ~ControlEvent() override = default;
        [[nodiscard]] Operation operation() const;

    private:
        Operation op;
    };
}

#endif //TANK_TROUBLE_CONTROL_EVENT_H
