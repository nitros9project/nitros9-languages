/*
 * time.h for KLibc, a superset of the Microware header it replaces in
 * /dd/defs: sgtbuf and tps are unchanged, and the rest is what KLibc's
 * time routines need, in K&R C for cc1.
 */
#ifndef _TIME_H_
#define _TIME_H_

#ifndef NULL
#define NULL 0
#endif

/* structure for the 'setime()' and 'getime()' calls */

struct sgtbuf {
        char    t_year,
                t_month,
                t_day,
                t_hour,
                t_minute,
                t_second;
};

/* system dependent value */
#ifdef LEVEL2
#define tps     100     /* ticks per second */
#else
#define tps     10      /* ticks per second */
#endif

/* time_t counts seconds since the Unix epoch, 1/1/1970 00:00:00 UTC */
typedef long time_t;

#define EPOCH_YEAR      1970
#define EPOCH_DOW       4       /* it was a Thursday */
#define TM_YEAR_BASE    1900

struct tm {
        int     tm_sec;         /* seconds (0 - 61) */
        int     tm_min;         /* minutes (0 - 59) */
        int     tm_hour;        /* hours (0 - 23) */
        int     tm_mday;        /* day of month (1 - 31) */
        int     tm_mon;         /* month of year (0 - 11) */
        int     tm_year;        /* years since 1900 */
        int     tm_wday;        /* day of week (Sunday = 0) */
        int     tm_yday;        /* day of year (0 - 365) */
        int     tm_isdst;       /* daylight saving time active */
};

extern int      daylight;       /* nonzero if DST is ever in use */
extern long     timezone;       /* signed offset from GMT in seconds */

extern time_t   time();         /* the current time, also in *arg if not NULL */
extern time_t   mktime();       /* from a struct tm */
extern time_t   cvtime();       /* from a setime/getime buffer */
extern struct tm *gmtime();     /* from a time_t, in GMT */
extern struct tm *localtime();  /* from a time_t, in the local time zone */
extern char     *asctime();     /* "Day Mon dd hh:mm:ss yyyy\n" from a struct tm */
extern char     *ctime();       /* asctime(localtime(timep)) */

#define difftime(t1,t0) ((long)(t1) - (long)(t0))

#endif
