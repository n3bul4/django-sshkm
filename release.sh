#!/bin/bash

############################################################################
### preconditions
############################################################################
# check parameter count
if [ "$2" == "" ]; then
    echo "usage: $0 <tag> <message>"
    exit 1
fi

# check correct working dir
#if [ ! -d .git -a ! -f setup.py ]; then
#    echo "please run this script from project base directory"
#    exit 2
#fi

# check if rpmbuild is installed
which rpmbuild >/dev/null 2>&1
if [ $? -ne 0 ]; then
    yum -y install rpmdevtools rpmlint
fi

# check if build environment is created
if [ ! -d ~/rpmbuild ]; then
    rpmdev-setuptree
fi
############################################################################


############################################################################
### prepare
############################################################################
# predefine variables
TAG=$1
MESSAGE="$2"
GITREPO=https://github.com/sshkm/django-sshkm.git
TEMPDIR=/tmp/sshkm-build
SPEC=rpmbuild/SPECS/sshkm.spec

# cleanup temp dir
rm -rf $TEMPDIR
mkdir -p $TEMPDIR

# clone git repo
cd $TEMPDIR
git clone $GITREPO

# get RPM release
#cd $TEMPDIR/django-sshkm
#RELEASE=$((($(grep "Release:" $SPEC | awk '{print $2}' | awk -F '%' '{print $1}')+1)))
RELEASE=1
############################################################################


############################################################################
### verify
############################################################################
# verify settings
echo "--------------------------------------------------------------"
echo "TAG: $TAG"
echo "MESSAGE: $MESSAGE"
echo "RPM RELEASE: $RELEASE"
echo ""
echo "---- please press enter to continue"
echo "--------------------------------------------------------------"
read
echo ""
############################################################################


############################################################################
### make changes for new version
############################################################################
# change to temporary directory
cd $TEMPDIR/django-sshkm

# set version in setup.py
sed -i "s/version = .*/version = '$TAG'/g" setup.py

# set version and releas in SPEC file
sed -i "s/Version:\t.*/Version:\t$TAG/g" $SPEC
sed -i "s/Release:\t.*/Release:\t$RELEASE%{?dist}/g" $SPEC
############################################################################


############################################################################
### commit changes and create tag
############################################################################
# change to temporary directory
cd $TEMPDIR/django-sshkm

# commit and push last modifications to git repo
git commit -a -m "$MESSAGE"
git push

# create tag and push it to git repo
git tag -a $TAG -m "$MESSAGE"
git push origin $TAG
############################################################################


############################################################################
### prepare files for pypi and upload them
############################################################################
# change to temporary directory
cd $TEMPDIR/django-sshkm

# prepare
python setup.py sdist
PYPIDIR=~/rpmbuild/pypi
rm -rf $PYPIDIR
mkdir -p $PYPIDIR
cp dist/* $PYPIDIR/
cp django_sshkm.egg-info/PKG-INFO $PYPIDIR/
############################################################################


############################################################################
### create SRPM
############################################################################
# change to temporary directory
cd $TEMPDIR/django-sshkm

# create tarball for rpmbuild
RPMSRC=$TEMPDIR/rpmbuild/SOURCES
mkdir -p $RPMSRC
cp -a rpmbuild/SOURCES/sshkm-master $RPMSRC/
mv $RPMSRC/sshkm-master $RPMSRC/sshkm-$TAG
cd $RPMSRC
tar czf ~/rpmbuild/SOURCES/sshkm-${TAG}.tar.gz sshkm-$TAG/

# build SRPM
cd $TEMPDIR/django-sshkm
rpmbuild -bs $TEMPDIR/django-sshkm/$SPEC
############################################################################


############################################################################
### cleanups
############################################################################
# cleanup temp dir
rm -rf $TEMPDIR
############################################################################


############################################################################
### final info
############################################################################
echo "--------------------------------------------------------------"
echo "manual steps:"
echo "- register pypi (files in $PYPIDIR)"
echo "- upload SRPM file to copr (file in ~/rpmbuild/SRPMS)"
echo "--------------------------------------------------------------"
############################################################################

