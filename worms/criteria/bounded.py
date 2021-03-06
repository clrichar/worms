from .base import *


class AxesIntersect(WormCriteria):
    """
    """

    def __init__(
            self,
            symname,
            tgtaxis1,
            tgtaxis2,
            from_seg=0,
            origin_seg=None,
            *,
            tolerance=1.0,
            lever=50,
            to_seg=-1,
            distinct_axes=False
    ):
        """
        """
        if from_seg == to_seg:
            raise ValueError('from_seg should not be same as to_seg')
        self.symname = symname
        self.from_seg = from_seg
        if len(tgtaxis1) == 2: tgtaxis1 += [0, 0, 0, 1],
        if len(tgtaxis2) == 2: tgtaxis2 += [0, 0, 0, 1],
        self.tgtaxis1 = (
            tgtaxis1[0], hm.hnormalized(tgtaxis1[1]), hm.hpoint(tgtaxis1[2])
        )
        self.tgtaxis2 = (
            tgtaxis2[0], hm.hnormalized(tgtaxis2[1]), hm.hpoint(tgtaxis2[2])
        )
        assert 3 == len(self.tgtaxis1)
        assert 3 == len(self.tgtaxis2)
        self.tgtangle = hm.angle(tgtaxis1[1], tgtaxis2[1])
        self.tolerance = tolerance
        self.lever = lever
        self.to_seg = to_seg
        self.rot_tol = tolerance / lever
        self.distinct_axes = distinct_axes  # -z not same as z (for T33)
        self.sym_axes = [self.tgtaxis1, self.tgtaxis2]
        self.is_cyclic = False
        self.origin_seg = None

    def score(self, segpos, verbosity=False, **kw):
        """TODO: Summary
        """
        cen1 = segpos[self.from_seg][..., :, 3]
        cen2 = segpos[self.to_seg][..., :, 3]
        ax1 = segpos[self.from_seg][..., :, 2]
        ax2 = segpos[self.to_seg][..., :, 2]
        if self.distinct_axes:
            p, q = hm.line_line_closest_points_pa(cen1, ax1, cen2, ax2)
            dist = hm.hnorm(p - q)
            cen = (p + q) / 2
            ax1c = hm.hnormalized(cen1 - cen)
            ax2c = hm.hnormalized(cen2 - cen)
            ax1 = np.where(hm.hdot(ax1, ax1c)[..., None] > 0, ax1, -ax1)
            ax2 = np.where(hm.hdot(ax2, ax2c)[..., None] > 0, ax2, -ax2)
            ang = np.arccos(hm.hdot(ax1, ax2))
        else:
            dist = hm.line_line_distance_pa(cen1, ax1, cen2, ax2)
            ang = np.arccos(np.abs(hm.hdot(ax1, ax2)))
        roterr2 = (ang - self.tgtangle)**2
        return np.sqrt(roterr2 / self.rot_tol**2 + (dist / self.tolerance)**2)

    def jit_lossfunc(self):
        from_seg = self.from_seg
        to_seg = self.to_seg
        if self.distinct_axes:
            raise NotImplementedError('T33 not supported yet')
        tgtangle = self.tgtangle
        tolerance = self.tolerance
        rot_tol = self.rot_tol

        @jit
        def func(pos, idx, verts):
            cen1 = pos[from_seg][:, 3]
            cen2 = pos[to_seg][:, 3]
            ax1 = pos[from_seg][:, 2]
            ax2 = pos[to_seg][:, 2]
            dist = hm.numba_line_line_distance_pa(cen1, ax1, cen2, ax2)
            ang = np.arccos(np.abs(hm.numba_dot(ax1, ax2)))
            roterr2 = (ang - tgtangle)**2
            return np.sqrt(roterr2 / rot_tol**2 + (dist / tolerance)**2)

        return func

    def alignment(self, segpos, debug=0, **kw):
        """
        """
        if hm.angle_degrees(self.tgtaxis1[1], self.tgtaxis2[1]) < 0.1:
            return np.eye(4)
        cen1 = segpos[self.from_seg][..., :, 3]
        cen2 = segpos[self.to_seg][..., :, 3]
        ax1 = segpos[self.from_seg][..., :, 2]
        ax2 = segpos[self.to_seg][..., :, 2]
        if not self.distinct_axes and hm.angle(ax1, ax2) > np.pi / 2:
            ax2 = -ax2
        p, q = hm.line_line_closest_points_pa(cen1, ax1, cen2, ax2)
        cen = (p + q) / 2
        # ax1 = hm.hnormalized(cen1 - cen)
        # ax2 = hm.hnormalized(cen2 - cen)
        x = hm.align_vectors(ax1, ax2, self.tgtaxis1[1], self.tgtaxis2[1])
        x[..., :, 3] = -x @ cen
        if debug:
            print(
                'angs', hm.angle_degrees(ax1, ax2),
                hm.angle_degrees(self.tgtaxis1[1], self.tgtaxis2[1])
            )
            print('ax1', ax1)
            print('ax2', ax2)
            print('xax1', x @ ax1)
            print('tax1', self.tgtaxis1[1])
            print('xax2', x @ ax2)
            print('tax2', self.tgtaxis2[1])
            raise AssertionError
            # if not (np.allclose(x @ ax1, self.tgtaxis1[1], atol=1e-2) and
            #         np.allclose(x @ ax2, self.tgtaxis2[1], atol=1e-2)):
            #     print(hm.angle(self.tgtaxis1[1], self.tgtaxis2[1]))
            #     print(hm.angle(ax1, ax2))
            #     print(x @ ax1)
            #     print(self.tgtaxis1[1])
            #     print(x @ ax2)
            #     print(self.tgtaxis2[1])
            #     raise AssertionError('hm.align_vectors sucks')

        return x

    def merge_segment(self, **kw):
        if self.origin_seg is None:
            return None
        return self.from_seg

    def stages(self, hash_cart_resl, hash_ori_resl, bbs, **kw):
        "return spearate criteria for each search stage"
        if self.origin_seg is None:
            return [(self, bbs)]
        raise NotImplementedError

    def which_mergeseg(self):
        "which bbs are being merged together"
        return (self.from_seg, )

    def iface_rms(self, pose0, prov, **kw):
        return -1


def D2(c2=0, c2b=-1, **kw):
    return AxesIntersect('D2', (2, Uz), (2, Ux), c2, to_seg=c2b, **kw)


def D3(c3=0, c2=-1, **kw):
    return AxesIntersect('D3', (3, Uz), (2, Ux), c3, to_seg=c2, **kw)


def D4(c4=0, c2=-1, **kw):
    return AxesIntersect('D4', (4, Uz), (2, Ux), c4, to_seg=c2, **kw)


def D5(c5=0, c2=-1, **kw):
    return AxesIntersect('D5', (5, Uz), (2, Ux), c5, to_seg=c2, **kw)


def D6(c6=0, c2=-1, **kw):
    return AxesIntersect('D6', (6, Uz), (2, Ux), c6, to_seg=c2, **kw)


def Tetrahedral(c3=None, c2=None, c3b=None, **kw):
    if 1 is not (c3b is None) + (c3 is None) + (c2 is None):
        raise ValueError('must specify exactly two of c3, c2, c3b')
    if c2 is None: from_seg, to_seg, nf1, nf2, ex = c3b, c3, 7, 3, 2
    if c3 is None: from_seg, to_seg, nf1, nf2, ex = c3b, c2, 7, 2, 3
    if c3b is None: from_seg, to_seg, nf1, nf2, ex = c3, c2, 3, 2, 7
    return AxesIntersect(
        'T',
        from_seg=from_seg,
        to_seg=to_seg,
        tgtaxis1=(max(3, nf1), hm.sym.tetrahedral_axes[nf1]),
        tgtaxis2=(max(3, nf2), hm.sym.tetrahedral_axes[nf2]),
        distinct_axes=(nf1 == 7),
        **kw
    )


def Octahedral(c4=None, c3=None, c2=None, **kw):
    if 1 is not (c4 is None) + (c3 is None) + (c2 is None):
        raise ValueError('must specify exactly two of c4, c3, c2')
    if c2 is None: from_seg, to_seg, nf1, nf2, ex = c4, c3, 4, 3, 2
    if c3 is None: from_seg, to_seg, nf1, nf2, ex = c4, c2, 4, 2, 3
    if c4 is None: from_seg, to_seg, nf1, nf2, ex = c3, c2, 3, 2, 4
    return AxesIntersect(
        'O',
        from_seg=from_seg,
        to_seg=to_seg,
        tgtaxis1=(nf1, hm.sym.octahedral_axes[nf1]),
        tgtaxis2=(nf2, hm.sym.octahedral_axes[nf2]),
        **kw
    )


def Icosahedral(c5=None, c3=None, c2=None, **kw):
    if 1 is not (c5 is None) + (c3 is None) + (c2 is None):
        raise ValueError('must specify exactly two of c5, c3, c2')
    if c2 is None: from_seg, to_seg, nf1, nf2, ex = c5, c3, 5, 3, 2
    if c3 is None: from_seg, to_seg, nf1, nf2, ex = c5, c2, 5, 2, 3
    if c5 is None: from_seg, to_seg, nf1, nf2, ex = c3, c2, 3, 2, 5
    return AxesIntersect(
        'I',
        from_seg=from_seg,
        to_seg=to_seg,
        tgtaxis1=(nf1, hm.sym.icosahedral_axes[nf1]),
        tgtaxis2=(nf2, hm.sym.icosahedral_axes[nf2]),
        **kw
    )


class Stack(WormCriteria):
    """
    """

    def __init__(self, sym, *, from_seg=0, tolerance=1.0, lever=50, to_seg=-1):
        if from_seg == to_seg:
            raise ValueError('from_seg should not be same as to_seg')
        self.sym = sym
        self.from_seg = from_seg
        self.tolerance = tolerance
        self.lever = lever
        self.to_seg = to_seg
        self.rot_tol = tolerance / lever
        self.is_cyclic = False
        self.symname = 'C' + str(self.sym)
        self.origin_seg = None

    def score(self):
        raise NotImplementedError

    def jit_lossfunc(self):
        from_seg = self.from_seg
        to_seg = self.to_seg
        tol2 = self.tolerance**2
        rot_tol2 = self.rot_tol**2

        @jit
        def func(pos, idx, verts):
            cen2 = pos[to_seg, :, 3].copy()  #  this was a good bug!
            ax2 = pos[to_seg, :, 2]
            cen2[2] = 0.0
            dist2 = np.sum(cen2**2)
            ang2 = np.arccos(np.abs(ax2[2]))**2
            err = np.sqrt(ang2 / rot_tol2 + dist2 / tol2)
            return err

        return func

    def alignment(self, segpos, debug=0, **kw):
        return np.eye(4)

    def merge_segment(self, **kw):
        return None

    def stages(self, hash_cart_resl, hash_ori_resl, bbs, **kw):
        "return spearate criteria for each search stage"
        return [(self, bbs)]

    def which_mergeseg(self):
        "which bbs are being merged together"
        return (self.from_seg, )

    def iface_rms(self, pose0, prov, **kw):
        return -1
