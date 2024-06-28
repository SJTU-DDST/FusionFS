ax.plot(*np.loadtxt(os.path.join(self.dat_dir, _get_data_file(fs)), unpack=True), label=label_fs(fs), color=c[0], marker=markers[0], lw=3, mec='black', markersize=8, alpha=1)
