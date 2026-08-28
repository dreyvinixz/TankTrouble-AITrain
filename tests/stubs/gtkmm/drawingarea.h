#ifndef GTKMM_STUB_DRAWINGAREA_H
#define GTKMM_STUB_DRAWINGAREA_H
#include "cairomm/context.h"

namespace Gtk {
    class DrawingArea {
    public:
        virtual bool on_draw(const Cairo::RefPtr<Cairo::Context>&) { return true; }
        virtual ~DrawingArea() = default;
    };
}

#endif // GTKMM_STUB_DRAWINGAREA_H
