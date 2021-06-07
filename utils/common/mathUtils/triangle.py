import vector
import line


class Triangle(object):
    """
    Triangle wrapper to get some triangle related data

    Args:
        point_a (list): triangle's first point position
        point_b (list): triangle's second point position
        point_c (list): triangle's third point position

    Examples:
        import utils.common.mathUtils as mathUtils

        triangle_obj = mathUtils.triangle.Triangle([10, 5, 7], [9, 0, -4], [0, 0, 0])

        # get normal vector
        normal = triangle_obj.normal
        # [-0.17518266842427596, 0.9021907423850212, -0.3941610039546209]

        # get area value
        triangle_obj.get_area()
        # 57.083272506050314

        # add input point to calculate data with triangle
        triangle_obj.input_point = [8, 7, -1]
        # get closest point on triangle, with barycentric coordinates weight values
        triangle_obj.closest_point()
        # ([8.9298757096823689, 2.2111400951357982, 1.0922203467853309],
        #  [0.44222801902715969, 0.50084394660119691, 0.056928034371643399])
    """
    def __init__(self, point_a, point_b, point_c):
        self._points = [point_a, point_b, point_c]
        self._vectors = []
        self._vec_cross = []
        self._normal = []

        self._area = 0

        self._input_point = [0, 0, 0]
        self._vector_point = []

        self._barycentric_dots = []
        self._barycentric_denom = []

        self._get_triangle_info()

    @property
    def points(self):
        """
        triangle's three points positions

        the triangle basic information (vectors, normal.. etc) will get recalculated automatically if set to a new
        position list
        """
        return self._points

    @property
    def normal(self):
        """
        triangle's normal vector
        """
        return self._normal

    @property
    def input_point(self):
        """
        point position if need to calculate data with the triangle
        need to give a point position to calculate data with the triangle, default position is [0, 0, 0]
        """
        return self._input_point

    @points.setter
    def points(self, pnts):
        self._points = pnts
        self._get_triangle_info()

    @input_point.setter
    def input_point(self, pnt):
        self._input_point = pnt
        self.get_point_info()

    def _get_triangle_info(self):
        """
        get triangle basic info for further data calculation,
        it includes two vectors shooting from the first point to the other two points (not normalized),
        cross product vector (normal vector without normalized)
        and the normal vector
        """
        self._vectors = [vector.create(self._points[0], self._points[1], normalize=False),
                         vector.create(self._points[0], self._points[2], normalize=False)]
        self._vec_cross = vector.cross_product(self._vectors[0], self._vectors[1], normalize=False)
        self._normal = vector.norm(self._vec_cross)

    def get_area(self):
        """
        get triangle's area value
        """
        self._area = vector.length(self._vec_cross) * 0.5
        return self._area

    def get_point_info(self):
        """
        get input point's basic info for further data calculation,
        it include vector shooting from the triangles first point to the input point (not normalized)
        """
        self._vector_point = vector.create(self._points[0], self._input_point, normalize=False)

    def closest_point_on_plane(self):
        """
        get the point projected on the triangle's infinity plane along normal vector with input point

        Returns: closest_point (list): projected point position
        """
        self.get_point_info()
        # get distance
        distance = vector.dot_product(self._vector_point, self._normal)
        # scale normal with distance
        normal_pnt = vector.scale(self._normal, -distance)
        # return closest point position
        return vector.add(self._points[0], self._vector_point, normal_pnt)

    def barycentric_coordinates(self):
        """
        get barycentric coordinates for the input point and the triangle

        Returns: weight_values (list): input point's weight values to each triangle points, the sum is 1
        """
        self._get_triangle_barycentric_info()
        u, v, w = self._get_barycentric_coordinates_for_point(self._input_point)
        return [u, v, w]

    def _get_triangle_barycentric_info(self):
        """
        get triangle barycentric coordinates information for further calculation
        when doing barycentric coordinates calculation for multiple points,
        should use this function combine with self._get_barycentric_coordinates_for_point(),
        not self.barycentric_coordinates(),
        that way we only calculate the triangle data once
        """
        dot_00 = vector.dot_product(self._vectors[0], self._vectors[0])
        dot_01 = vector.dot_product(self._vectors[0], self._vectors[1])
        dot_11 = vector.dot_product(self._vectors[1], self._vectors[1])
        denom = (dot_00 * dot_11 - dot_01 * dot_01)
        denom_inv = 1.0 / denom

        self._barycentric_dots = [dot_00, dot_01, dot_11]
        self._barycentric_denom = [denom, denom_inv]

    def _get_barycentric_coordinates_for_point(self, pnt):
        """
        get barycentric coordinates for the given point and the triangle
        need to run self._get_triangle_barycentric_info() first to get triangle data

        Args:
            pnt (list): given point position

        Returns:
            weight_values (list): given point's weight values to each triangle points, the sum is 1
        """
        vector_point = vector.create(self._points[0], pnt, normalize=False)
        dot_20 = vector.dot_product(vector_point, self._vectors[0])
        dot_21 = vector.dot_product(vector_point, self._vectors[1])

        v = (self._barycentric_dots[2] * dot_20 - self._barycentric_dots[1] * dot_21) * self._barycentric_denom[1]
        w = (self._barycentric_dots[0] * dot_21 - self._barycentric_dots[1] * dot_20) * self._barycentric_denom[1]
        u = 1 - v - w
        return [u, v, w]

    def if_inside(self):
        """
        check if the given point inside the triangle

        Returns: in_triangle (bool): True / False
                 weight_values (list): input point's barycentric coordinates weight values to each triangle points,
                                       the sum is 1
        """
        in_triangle, [u, v, w] = self._if_point_inside(self._input_point)
        return in_triangle, [u, v, w]

    def _if_point_inside(self, pnt):
        """
        check if given point is inside the triangle,
        need to run self._get_triangle_barycentric_info() first to get triangle data

        Args:
            pnt (list): given point position

        Returns: in_triangle (bool): True / False
                 weight_values (list): given point's barycentric coordinates weight values to each triangle points,
                                       the sum is 1

        """
        in_triangle = False
        # get barycentric coordinates
        u, v, w = self._get_barycentric_coordinates_for_point(pnt)
        # check to see if values all in range [0, 1]
        if 0 <= u <= 1 and 0 <= v <= 1 and 0 <= w <= 1:
            in_triangle = True
        return in_triangle, [u, v, w]

    def closest_point(self):
        """
        closest point projected on triangle with the input point,
        first it will project the point onto the triangle's plane,
        it will use the point if it's inside the triangle,
        otherwise will try to project the point to the triangle's boundary to get the closest point

        Returns:
            closest_point (list): closest point position
            weight_values (list): input point's barycentric coordinates weight values to each triangle points,
                                  the sum is 1
        """
        # get point projected on plane
        cls_pnt = self.closest_point_on_plane()
        # get triangle's barycentric info data
        self._get_triangle_barycentric_info()
        # check values to see if it's in triangle
        in_triangle, [u, v, w] = self._if_point_inside(cls_pnt)
        if not in_triangle:
            cls_pnt = self.closest_point_on_boundary(cls_pnt)
            u, v, w = self._get_barycentric_coordinates_for_point(cls_pnt)

        return cls_pnt, [u, v, w]

    def closest_point_on_boundary(self, point_pos):
        """
        project the given point to the triangle's boundary to get the closest point

        Args:
            point_pos (list): given point position

        Returns:
            closest_point (list): closest point position
        """
        # get closest point on all three lines
        pnt_a, param = line.closest_point([self._points[0], self._points[1]], point_pos, clamp=True)
        pnt_b, param = line.closest_point([self._points[0], self._points[2]], point_pos, clamp=True)
        pnt_c, param = line.closest_point([self._points[1], self._points[2]], point_pos, clamp=True)

        # get vectors from point to three points
        vec_a = vector.create(point_pos, pnt_a, normalize=False)
        vec_b = vector.create(point_pos, pnt_b, normalize=False)
        vec_c = vector.create(point_pos, pnt_c, normalize=False)

        # get length
        dis_a = vector.length(vec_a)
        dis_b = vector.length(vec_b)
        dis_c = vector.length(vec_c)

        # get minimize length
        dis_min = min(dis_a, dis_b, dis_c)

        # get point with min value
        if dis_a == dis_min:
            cls_pnt = pnt_a
        elif dis_b == dis_min:
            cls_pnt = pnt_b
        else:
            cls_pnt = pnt_c

        return cls_pnt
