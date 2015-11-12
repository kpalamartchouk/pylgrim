#!/usr/bin/python
#! encoding: UTF8
__author__ = 'kirienko'

import re
from collections import defaultdict

from nav_data import NavGPS, NavGLO
from obs_data import ObsGPS


def get_header_line(headr,property):
    '''
    :param headr: the header of the RINEX-file
    :param property: string-like property to search for (e.g. 'delta-utc')
    :return: the string of the ``headr`` containing ``property``
    '''
    pattern = re.compile(property, re.IGNORECASE)
    for d in headr:
        if pattern.search(d):
            return d

def parse_rinex(path):
    """
    Parse RINEX-file and returns a timeline, i.e. array of tuples
        (time_of_event, Object_instance),
    where Object_instance is either Nav or Observ depending on the type of RINEX file (detected automatically).
    :param path: path to RINEX file
    :return: timeline
    """

    with open(path) as fd:
        data = fd.readlines()
        for j,d in enumerate(data):
            if "END OF HEADER" in d:
                header_end = j
                break
    header, body = data[:header_end], data[header_end+1:]

    # Define RINEX file properties
    rinex_version = re.findall('[0-9]'+'\.'+'[0-9]+',header[0][:60])[0]
    pat_file = re.compile("nav|obs",re.IGNORECASE)
    pat_satel = re.compile("gps|glo|mix",re.IGNORECASE)
    rinex_type = re.findall(pat_file,header[0][:60])[0].lower()
    satel_type = re.findall(pat_satel,header[0][:60])[0].lower()
    print "\n\nParsing %s:" % path
    print "RINEX version:", rinex_version
    print "RINEX type:", rinex_type

    if rinex_type == 'nav':
        # Define UTC conversion data
        utc = get_header_line(header,'delta-utc')
        LEAP = int(get_header_line(header,'leap')[:60])
        A0,A1 = [float(h.replace('D','E')) for h in [utc[:22],utc[22:41]]]
        T,W = map(int,utc[42:60].split())

        print "Satellites:", satel_type
        print "utc: A0 = %e, A1 = %e, T = %d, W = %d, leap seconds: %d" % (A0,A1,T,W, LEAP)

    prefixes = {'gps':'G', 'glo':'R', 'mix': 'M'}
    sat_prefix = prefixes[satel_type]

    if rinex_type == 'nav' and satel_type != 'mix':

        if satel_type == 'gps':
            if len(body) % 8 != 0:
                print "Warning: wrong length of NAV file"
            nav_list = [NavGPS(body[i*8:(i+1)*8],(LEAP,A0,A1)) for i in xrange(len(body)/8)]
        elif satel_type == 'glo':
            if len(body) % 4 != 0:
                print "Warning: wrong length of NAV file"
            nav_list = [NavGLO(body[i*4:(i+1)*4],(LEAP,A0,A1)) for i in xrange(len(body)/4)]
        nav_dict = defaultdict(list)
        for obj in nav_list:
            nav_dict[sat_prefix+"%02d"%obj.PRN_number] += [obj]
        return nav_dict

    elif rinex_type == 'obs':
        obs_types = get_header_line(header,"TYPES OF OBSERV").split()
        number_of_obs_types = int(obs_types[0])
        obs_types = obs_types[1:1+number_of_obs_types]
        # print obs_types


        # for h in header: print h,
        observations = []
        for j,h in enumerate(body):
            # print j
            if h[:4] == ' 15 ':
                satellite_count = int(h[30:32])
                observations += [ObsGPS(body[j:j+satellite_count+1],obs_types)]
        return observations
    else:
        raise NotImplementedError


if __name__ == "__main__":

    navigations = parse_rinex('../test_data/test.n')
    # for k,v in navigations.items(): print k, [str(vv.date)for vv in v]
    # print "\nSatellites:", ', '.join(sorted(navigations.keys()))
    g = navigations['G05']
    # g = navigations['R04']
    z1,z2 = sorted([g[0],g[1]],key=lambda x: x.date)
    t1,t2 = z1.eph[8], z2.eph[8]

    # delta_t = dt.timedelta(seconds=t2-t1)
    # print "Δt = t1 - t2 = %s" % delta_t
    # R1, R2 = z1.eph2pos(z1.date+delta_t/2),z2.eph2pos(z2.date-delta_t/2)
    # print "R(t1 - Δt/2) = ",R1
    # print "R(t2 + Δt/2) = ",R2
    # print "ΔX = %d km, ΔY = %d km, ΔZ = %d km" % tuple(int((r2-r1)) for r1,r2 in zip(R1,R2))

    observations = parse_rinex('../test_data/test.o')