/*
 *     Find and update file modification times
 *       This program has been placed in the Public Domain.
 */

#include <stdio.h>
#ifdef unix
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/errno.h>
#include <time.h>
#include <utime.h>
#endif
#ifdef eon
#include <sys/stat.h>
#include <sys/err.h>
#endif
#ifdef OS9
#include <time.h>
#include <os.h>
#include <fcntl.h>
#include <errno.h>
#endif
#include "h.h"



#ifdef OS9
/*
 *     Some stuffing around to get the modified time of a file
 *     in an OS9 file system
 */
int getmdate(int fd, _os_time *packet)
{
       static char descriptor[256];
       int count = sizeof(descriptor);
       if (_os_gs_fd(fd, descriptor, &count))
               return -1;
       if (packet) {
               /* RBF FD.DAT at byte 3 contains year/month/day/hour/minute. */
               memcpy(packet, descriptor + 3, 5);
               packet->seconds = 0;
       }
       return 0;
}

#endif


/*
 *     Get the modification time of a file.  If the first
 *     doesn't exist, it's modtime is set to 0.
 */
void
modtime(struct name *np)
{
#ifdef unix
       struct stat             info;
       int                     fd;


       if (stat(np->n_name, &info) < 0)
       {
               if (errno != ENOENT)
                       fatal("Can't open %s; error %d", np->n_name, errno);

               np->n_time = 0L;
       }
       else
               np->n_time = info.st_mtime;
#endif
#ifdef eon
       struct stat             info;
       int                     fd;


       if ((fd = open(np->n_name, 0)) < 0)
       {
               if (errno != ER_NOTF)
                       fatal("Can't open %s; error %d", np->n_name, errno);

               np->n_time = 0L;
       }
       else if (getstat(fd, &info) < 0)
               fatal("Can't getstat %s; error %d", np->n_name, errno);
       else
               np->n_time = info.st_mod;

       close(fd);
#endif
#ifdef OS9
       _os_time              info;
       int                     fd;
       int                     mode=0;
       char *                  suff;
       char                    fullname[256];
       
       suff=suffix(np->n_name);
       fullname[0]='\0';
       
       if ((suff == (char *)0 ) && (rules)) { /* Is this an executable? */
               mode = 4;
               strcpy(fullname,object_dir);
               if (strlen(object_dir) != 0)
                       strcat(fullname,"/");
       } else if ((strcmp(suff,".r")==0) && (rules)) {  /* Is it .r ?? */
               strcpy(fullname,rel_dir);
               if (strlen(rel_dir) != 0)
                       strcat(fullname,"/");
       }
       strcat(fullname,np->n_name);

       if (((fd = open(fullname, mode)) < 0) &&   /* Check mode first */
           ((fd = open(fullname,  0  )) < 0))    /* Then data dir */
       {
               if (errno != E_PNNF)
                       fatal("Can't open %s with mode %d; error %d",
                             fullname, mode, errno);
               if (debug)
                  printf("\"%s\" does not exist, timestamp = 0.\n",fullname);

               np->n_time = 0L;
       }
       else if (getmdate(fd, &info) < 0)
               fatal("Can't getstat %s; error %d", np->n_name, errno);
       else {
               np->n_time = o2utime(&info);
       }
       if (debug && (np->n_time != 0L)) {
               printf("\"%s\" was last modified",fullname);
               printf(" %3d/%02d/%02d  %2d:%02d; timestamp %ld.\n",
                     info.year,info.month,info.day,info.hours,
                     info.minutes,np->n_time);
       }   

       close(fd);
#endif
}


/*
 *     Update the mod time of a file to now.
 */
void
touch(struct name *np)
{
       char                    c;
       int                     fd;


       if (!domake || !silent)
               printf("    touch(%s)\n", np->n_name);

       if (domake)
       {
#ifdef unix
               struct utimbuf  a;

               a.actime = a.modtime = time(0);
               if (utime(np->n_name, &a) < 0)
                       printf("%s: '%s' not touched - non-existent\n",
                                       myname, np->n_name);
#endif
#ifdef eon
               if ((fd = open(np->n_name, 0)) < 0)
                       printf("%s: '%s' not touched - non-existent\n",
                                       myname, np->n_name);
               else
               {
                       uread(fd, &c, 1, 0);
                       uwrite(fd, &c, 1);
               }
               close(fd);
#endif
#ifdef OS9
               /*
                *      Strange that something almost as totally useless
                *      as this is easy to do in OS9!
                */
               int                     mode=0;
               char *                  suff;
               char                    fullname[256];
       
               suff=suffix(np->n_name);
               fullname[0]='\0';

               if ((suff == (char *)0 ) && (rules)) { /* Is this an exec? */
                       mode = 4;
                       strcpy(fullname,object_dir);
                       if (strlen(object_dir) != 0)
                               strcat(fullname,"/");
               } else if ((strcmp(suff,".r")==0) && (rules)) { /*Is it .r ?*/
                       strcpy(fullname,rel_dir);
                       if (strlen(rel_dir) != 0)
                               strcat(fullname,"/");
               }
               strcat(fullname,np->n_name);

               if (debug)
                   printf("Touching %s with mode %d.\n",fullname,mode);

               if ((fd = open(fullname, S_IWRITE | mode )) < 0) {
                       printf("%s: '%s' not touched - non-existent.\n",
                                       myname, fullname);
               }
               close(fd);
#endif
       }
}
