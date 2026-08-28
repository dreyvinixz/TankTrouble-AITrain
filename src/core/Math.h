//
// Created by zr on 23-2-8.
//

#ifndef TANK_TROUBLE_MATH_H
#define TANK_TROUBLE_MATH_H
#include <vector>
#include <utility>
#include "Vec.h"

namespace TankTrouble::util
{
    // Convert between radians and degrees.
    double rad2Deg(double rad);

    double deg2Rad(double deg);

    // Calculate a rotation angle from a vector.
    double vector2Angle(const util::Vec& v);

    Vec polar2Cart(double theta, double p, Vec O = Vec(0, 0));

    // Calculate a rectangle's four vertices from its center, rotation, width, and height.
    std::vector<Vec> getCornerVec(const Vec& pos, double angle, int w, int h);

    // Test a rectangle and circle for collision using the rectangle axes, centers, dimensions, and radius.
    bool checkRectCircleCollision(const Vec& vec1, const Vec& vec2,
                                  const Vec& rectCenter, const Vec& circleCenter,
                                  int width, int height, double r);

    // Calculate a line's general form from two points.
    void twoPointToGeneral(Vec p1, Vec p2, double* A, double* B, double* C);

    // Find the intersection of two lines in general form.
    bool intersectionOfLines(double A1, double B1, double C1, double A2, double B2, double C2, Vec* p);

    // Find the intersection of two line segments.
    bool intersectionOfSegments(Vec p1, Vec p2, Vec p3, Vec p4, Vec* i);

    // Reflect an angle across the X axis.
    double angleFlipX(double angle);

    // Reflect an angle across the Y axis.
    double angleFlipY(double angle);

    // Get a rectangle's two unit test axes from its rotation.
    std::pair<Vec, Vec> getUnitVectors(double angleDeg);

    util::Vec getUnitVector(double angleDeg);

    // Test two rectangles for collision (angle is the rotation angle).
    bool checkRectRectCollision(double angle1, Vec center1, double W1, double H1,
                                double angle2, Vec center2, double W2, double H2);

    // Distance between two points.
    double distanceOfTwoPoints(const Vec& p1, const Vec& p2);

    // Angle between two vectors, in degrees.
    double angleBetweenVectors(const Vec& v1, const Vec& v2);

    void setRandomSeed(unsigned int seed);
    int getRandomNumber(int low, int high);
}

#endif //TANK_TROUBLE_MATH_H
