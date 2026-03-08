from typing import Literal, Optional

from pydantic import BaseModel


class KaryawanCreateRequest(BaseModel):
  id_karyawan: str
  nama_karyawan: str
  email_karyawan: str | None = None
  nomor_hp: str | None = None
  tanggal_rekrut: str | None = None
  status: str = "aktif"
  id_departemen: int
  posisi: str | None = None


class AkunCreateRequest(BaseModel):
  username: str
  passwd: str
  roles: str = "karyawan"
  id_karyawan: str
  status: str = "aktif"


class DepartemenCreateRequest(BaseModel):
  nama_departemen: str


class KaryawanUpdateRequest(BaseModel):
  nama_karyawan: str
  email_karyawan: str | None = None
  nomor_hp: str | None = None
  tanggal_rekrut: str | None = None
  status: str
  id_departemen: int
  posisi: str | None = None


class AkunUpdateRequest(BaseModel):
  passwd: str
  roles: str
  id_karyawan: str
  status: bool


class KonfigurasiUpdateRequest(BaseModel):
  id_pengaturan: int
  toleransi_terlambat: int
  maks_hari_cuti: int


class JadwalUpdateRequest(BaseModel):
  shift_mulai: str | None = None
  shift_selesai: str | None = None


class HariLiburCreateRequest(BaseModel):
  tanggal: str
  keterangan: str
  tipe: Literal["libur_nasional", "cuti_bersama"]


class HariLiburUpdateRequest(BaseModel):
  tanggal: str
  keterangan: str
  tipe: Literal["libur_nasional", "cuti_bersama"]


class UpdateStatusAbsensiRequest(BaseModel):
  status_absen: str
  alasan_penolakan: str | None = None
  id_karyawan: str
  id_absensi: int
  updated_bulk_data: list[dict] | None = None


class UpdatePengajuanRequest(BaseModel):
  id_pengajuan: int
  id_karyawan: str
  status: str
  tipe_pengajuan: str
  tanggal_mulai: str
  tanggal_akhir: str
  alasan_penolakan: str | None = None
