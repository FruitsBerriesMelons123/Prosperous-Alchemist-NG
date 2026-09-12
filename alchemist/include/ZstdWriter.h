#pragma once

#include <zstd.h>
#include <cstdio>
#include <filesystem>
#include <stdexcept>
#include <string_view>
#include <vector>

class ZstdWriter {
public:
	explicit ZstdWriter(const std::filesystem::path& filepath, int compressionLevel = 3)
	{
#ifdef _WIN32
		_file = _wfopen(filepath.c_str(), L"wb");
#else
		_file = fopen(filepath.string().c_str(), "wb");
#endif
		if (!_file) {
			throw std::runtime_error("Failed to open output file.");
		}

		_cctx = ZSTD_createCCtx();
		if (!_cctx) {
			fclose(_file);
			_file = nullptr;
			throw std::runtime_error("Failed to create ZSTD compression context.");
		}
		ZSTD_CCtx_setParameter(_cctx, ZSTD_c_compressionLevel, compressionLevel);

		_outBuff.resize(ZSTD_CStreamOutSize());
	}

	~ZstdWriter()
	{
		close();
	}

	void write(std::string_view data)
	{
		if (!_cctx || !_file) return;
		ZSTD_inBuffer in = { data.data(), data.size(), 0 };
		while (in.pos < in.size) {
			ZSTD_outBuffer out = { _outBuff.data(), _outBuff.size(), 0 };
			size_t const result = ZSTD_compressStream2(_cctx, &out, &in, ZSTD_e_continue);
			if (ZSTD_isError(result)) {
				throw std::runtime_error(ZSTD_getErrorName(result));
			}
			if (out.pos > 0) {
				fwrite(_outBuff.data(), 1, out.pos, _file);
			}
		}
	}

	void writeLine(std::string_view line)
	{
		write(line);
		write("\n");
	}

	void close()
	{
		if (!_cctx || !_file) return;

		ZSTD_inBuffer in = { nullptr, 0, 0 };
		size_t remaining = 0;
		do {
			ZSTD_outBuffer out = { _outBuff.data(), _outBuff.size(), 0 };
			remaining = ZSTD_compressStream2(_cctx, &out, &in, ZSTD_e_end);
			if (ZSTD_isError(remaining)) {
				break;
			}
			if (out.pos > 0) {
				fwrite(_outBuff.data(), 1, out.pos, _file);
			}
		} while (remaining > 0);

		ZSTD_freeCCtx(_cctx);
		fclose(_file);
		_cctx = nullptr;
		_file = nullptr;
	}

private:
	FILE* _file = nullptr;
	ZSTD_CCtx* _cctx = nullptr;
	std::vector<uint8_t> _outBuff;
};
