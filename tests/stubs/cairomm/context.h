#ifndef CAIROMM_STUB_CONTEXT_H
#define CAIROMM_STUB_CONTEXT_H

namespace Cairo {
    template <typename T>
    class RefPtr {
    public:
        RefPtr() : ptr_(nullptr) {}
        explicit RefPtr(T* p) : ptr_(p) {}
        T* operator->() const { return ptr_; }
        T* get() const { return ptr_; }
    private:
        T* ptr_;
    };

    class Context {
    public:
        void save() {}
        void restore() {}
        void close_path() {}
        void fill() {}
        void stroke() {}
        void set_source_rgb(double, double, double) {}
        void set_line_width(double) {}
        void move_to(double, double) {}
        void line_to(double, double) {}
        void arc(double, double, double, double, double) {}
    };
}

#endif // CAIROMM_STUB_CONTEXT_H
