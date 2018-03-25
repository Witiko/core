import os

from ocrd.model import OcrdMets
from ocrd.utils import getLogger
log = getLogger('ocrd.workspace')

class Workspace(object):
    """
    A workspace is a temporary directory set up for a processor. It's the
    interface to the METS/PAGE XML and delegates download and upload to the
    Resolver.
    """

    def __init__(self, resolver, directory):
        self.resolver = resolver
        self.directory = directory
        self.mets_filename = os.path.join(directory, 'mets.xml')
        self.mets = OcrdMets(filename=self.mets_filename)

    def __str__(self):
        return 'Workspace[directory=%s, file_groups=%s, files=%s]' % (
            self.directory,
            self.mets.file_groups,
            [str(f) for f in self.mets.files],
        )

    def download_url(self, url, **kwargs):
        """
        Download a URL to the workspace.
        """
        return self.resolver.download_to_directory(self.directory, url, **kwargs)

    @property
    def pages(self):
        self.mets.files_in_group('INPUT')

    def download_file(self, f, **kwargs):
        """
        Download a ~OcrdFile to the workspace.
        """
        if f.local_filename:
            log.debug("Alrady downloaded: %s", f.local_filename)
        else:
            f.local_filename = self.download_url(f.url, **kwargs)
        return f

    def download_files_in_group(self, use):
        """
        Download all  the ~OcrdFile in the file group given.
        """
        for input_file in self.mets.files_in_group(use):
            self.download_file(input_file, subdir=use)

    def add_file(self, use, basename=None, content=None, local_filename=None, **kwargs):
        """
        Add an output file. Creates an ~OcrdFile to pass around and adds that to the
        OcrdMets OUTPUT section.
        """
        log.debug('outputfile use=%s basename=%s local_filename=%s content=%s', use, basename, local_filename, content is not None)
        if basename is not None:
            if use is not None:
                basename = os.path.join(use, basename)
            local_filename = os.path.join(self.directory, basename)

        local_filename_dir = local_filename.rsplit('/', 1)[0]
        if not os.path.isdir(local_filename_dir):
            os.makedirs(local_filename_dir)

        if 'url' not in kwargs:
            kwargs['url'] = 'file://' + local_filename

        self.mets.add_file(use, local_filename=local_filename, **kwargs)

        if content is not None:
            with open(local_filename, 'wb') as f:
                f.write(content)

    def persist(self):
        """
        Persist the workspace using the resolver. Uploads the files in the
        OUTPUT group to the data repository, sets their URL accordingly.
        """
        self.save_mets()
        # TODO: persist file:// urls

    def save_mets(self):
        """
        Write out the current state of the METS file.
        """
        with open(self.mets_filename, 'wb') as f:
            f.write(self.mets.to_xml())
