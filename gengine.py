from math import sin, asin, cos, acos, log, tan, atan2
from math import sqrt, radians, degrees, pi

# -----------------------------------------------
# CONSTANTS
# -----------------------------------------------
KM2MILES: float = 0.621371  # Multiply km to get miles
R45: float = .7854          # 45 degrees in radians


# -----------------------------------------------
# Global variables and default values
# -----------------------------------------------
geomodel: str = 'WGS-84'        # either 'WGS-84' or 'Sphere'
bminor: float = 6356.752314245  # WGS-84 minor semiaxis (km)
amajor: float = 6378.137        # WGS-84 major semiaxis (km)
f: float = 0.0033528            # WGS-84 Flattening from sphere
ecc: float = 0.08181919         # WGS-84 spherical eccentricity
keepd: dict = {}                # Dictionary for logging variables


# -----------------------------------------------
# Classes
# -----------------------------------------------
class Location():
    def __init__(self, lat: str, lon: str):
        self._lat: str = lat
        self._lon: str = lon
        self._dlat: float = float(self._lat)
        self._dlon: float = float(self._lon)

    @property
    def rlat(self):
        return radians(self._dlat)

    @property
    def rlon(self):
        return radians(self._dlon)


class GeoPath():
    def __init__(self, distance: float, course: float):
        self._dkm: float = distance
        self._rc: float = course
        self._distancemi: float = self._dkm * KM2MILES
        self._dcourse: float = degrees(self._rc)

    @property
    def distance(self):
        return f"{self._distancemi:.2f} miles"

    @property
    def course(self):
        return f"{self._dcourse:.2f}° true"


# -----------------------------------------------
# Functions
# -----------------------------------------------

def sec(a: float) -> float:
    '''
    Roll your own Secant function
    '''
    return 1/cos(a)


def radius_model(model: str) -> None:
    '''
    Set all Geo modeling variables for WGS-84 or Sphere
    Called by geocalc.do_calc before each calculation
    '''
    global geomodel, bminor, amajor, F, Ecc
    if model == 'WGS-84':
        geomodel = model
        bminor = 6356.752314245
        amajor = 6378.137
        f = (amajor-bminor) / amajor
        ecc = sqrt(1 - (bminor**2/amajor**2))
    else:  # for anything else recert to Sphere
        geomodel = model
        bminor = 6371.088
        amajor = 6371.088
        f = 0
        ecc = 0
    keepd['radius'] = geomodel


def rhumb(gfrom: Location, gto: Location) -> GeoPath:
    '''
    Rhumb line calculator:
    Distance from one location to another on constant bearing
    --- Longer than a Great Circle route
    --- Compensates for flatend ellipse (WGS84)
    Inputs: Latitude and Longitude in radians via Location class
    Returns: distance (km) and bearing (rad) via GeoPath class
    '''

    keepd['FromLatR'] = lat1r = gfrom.rlat
    keepd['FromLonR'] = lon1r = gfrom.rlon
    keepd['ToLatR'] = lat2r = gto.rlat
    keepd['ToLonR'] = lon2r = gto.rlon
    keepd['rhbminor'] = bminor
    keepd['rhecc'] = ecc

    # delta longitude for bearing angle calc
    dLonr: float = 0
    dr: float = lon2r - lon1r
    if abs(dr) <= pi:      # within +/- 180 degrees of point #1
        dLonr = lon2r - lon1r
    elif (dr) < -pi:       # more than 180 degrees west
        dLonr = 2*pi + lon2r - lon1r
    elif (dr) > pi:        # more than 180 degrees east
        dLonr = lon2r - lon1r - 2*pi

    # Bearing calculation (radians)
    # Breaking formula into pieces for convenience
    x2: float = tan((pi/4)+(lat2r/2)) \
        * (((1-ecc*sin(lat2r)) / (1+ecc*sin(lat2r))))**(ecc/2)
    x1: float = tan((pi/4)+(lat1r/2)) \
        * (((1-ecc*sin(lat1r)) / (1+ecc*sin(lat1r))))**(ecc/2)
    angler: float = atan2(dLonr, log(x2) - log(x1))

    # Rhumb length calculation (km)
    # Break calculation into pieces
    dLatr: float = lat2r - lat1r
    xLat: float = (1 - (1/4) * ecc**2)*dLatr - \
                  (3/8) * ecc**2 * (sin(2*lat2r) - sin(2*lat1r))
    rhumbLenght: float = amajor * sec(angler) * xLat

    keepd['angler'] = angler
    keepd['rlength'] = rhumbLenght
    keepd['Rhumb'] = 'Ok'

    return GeoPath(rhumbLenght, angler)


def greatcircle(gfrom: Location, gto: Location) -> GeoPath:
    '''
    Great Circle calculator:
    Shortest istance from one location to another
    --- Compensates for flatend sphere (WGS84)
    Inputs: Latitude and Longitude in radians via Location class
    Returns: distance (km) and initial course (rad) via GeoPath class

    Vincenty Great Circle distance
    Python adapted from JavaScript by Chris Veness (2002)
    see  http://www.movable-type.co.uk/scripts/latlong-vincenty.html

    '''

    lat1r: float = gfrom.rlat
    lon1r: float = gfrom.rlon
    lat2r: float = gto.rlat
    lon2r: float = gto.rlon

    gclength: float = 100   # (km) a default value
    courser: float = R45    # (radians) a default value

    # greek letters for use in Vincenty variable names below
    # ----------------------------------------------------------------
    # 𝝺  := difference in longitude on an auxiliary sphere
    # 𝝈  := angular distance point to point on sphere
    # 𝝈m := angular distance on sphere from equator to midpoint on line
    # 𝝰  := azimuth of the geodesic at the equator

    # Calculate only once
    tanU1 = (1-f)*tan(lat1r)
    tanU2 = (1-f)*tan(lat2r)
    cosU1 = 1 / sqrt(1+tanU1*tanU1)
    cosU2 = 1 / sqrt(1+tanU2*tanU2)
    sinU1 = tanU1 * cosU1
    sinU2 = tanU2 * cosU2

    deltaLonr = lon2r - lon1r

    # some initial conditions ** assumes not antipodal
    𝞂 = 0
    sin𝞂 = 0
    cos𝞂 = 1
    cos2𝞂m = 1
    cosSq𝞪 = 1

    # iterate until change in 𝝺 is negligible
    𝝺 = deltaLonr
    𝝺0 = 0      # previous 𝝺
    while True:
        sin𝝺 = sin(𝝺)
        cos𝝺 = cos(𝝺)
        sinSq𝞂 = (cosU2*sin𝝺) * (cosU2*sin𝝺) +\
                 (cosU1*sinU2-sinU1*cosU2*cos𝝺)**2
        sin𝞂 = sqrt(sinSq𝞂)
        cos𝞂 = sinU1*sinU2 + cosU1*cosU2*cos𝝺
        𝞂 = atan2(sin𝞂, cos𝞂)
        sin𝞪 = cosU1*cosU2*sin𝝺/sin𝞂
        cosSq𝞪 = 1 - sin𝞪*sin𝞪
        cos2𝞂m = cos𝞂 - 2*sinU1*sinU2/cosSq𝞪
        C = f/16 * cosSq𝞪 * (4+f*(4-3*cosSq𝞪))
        𝝺0 = 𝝺
        𝝺 = deltaLonr + (1-C) * f * sin𝞪 *\
            (𝞂 + C*sin𝞂*(cos2𝞂m+C*cos𝞂*(-1+2*cos2𝞂m*cos2𝞂m)))
        if abs(𝝺0 - 𝝺) < 1E-12:   # 𝝺 has converged
            break

    # Finish calculations

    uSq = cosSq𝞪 * (amajor*amajor - bminor*bminor) / (bminor*bminor)
    A = 1 + uSq/16384 * (4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    delta𝞂 = B*sin𝞂*(cos2𝞂m+B/4*(cos𝞂*(-1+2*cos2𝞂m*cos2𝞂m) -
                     B/6*cos2𝞂m*(-3+4*sin𝞂*sin𝞂)*(-3+4*cos2𝞂m*cos2𝞂m)))

    gclength = bminor*A*(𝞂-delta𝞂)
    courser = atan2(cosU2*sinλ, cosU1*sinU2-sinU1*cosU2*cosλ)

    keepd['gclength'] = gclength
    keepd['gccourser'] = courser
    keepd['GC'] = 'Ok'

    return GeoPath(gclength, courser)


if __name__ == "__main__":

    ll = Location(lat="45.56", lon="-122.2")
    print(f'String "{ll._lat}"')
    print(f"{ll._dlat:8.4f} degrees")
    print(f"{ll.rlat:8.4f} radians")
