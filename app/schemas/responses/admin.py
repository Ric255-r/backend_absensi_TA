from datetime import date, datetime, time

from pydantic import BaseModel


class HariLiburResponse(BaseModel):
  id_libur: int
  tanggal: date
  keterangan: str
  tipe: str


class KaryawanItemResponse(BaseModel):
  id_karyawan: str
  nama_karyawan: str
  email_karyawan: str | None = None
  nomor_hp: str | None = None
  foto_profile: str | None = None
  tanggal_rekrut: date | None = None
  status: str
  posisi: str | None = None
  departemen_id: int
  departemen__nama_departemen: str | None = None


class AkunItemResponse(BaseModel):
  username: str
  roles: str
  status: str
  last_login: datetime | None = None
  device_id: str | None = None
  karyawan_id: str


class DepartemenItemResponse(BaseModel):
  id_departemen: int
  nama_departemen: str


class JadwalItemResponse(BaseModel):
  id_jadwal: int
  hari_dalam_seminggu: str
  shift_mulai: str | None = None
  shift_selesai: str | None = None


class JadwalMingguanKaryawanItemResponse(BaseModel):
  id: int
  id_karyawan: str
  hari: str
  kode_shift: str


class KonfigurasiItemResponse(BaseModel):
  id_pengaturan: int
  toleransi_terlambat: int
  maks_hari_cuti: int


class DashboardKaryawanCountResponse(BaseModel):
  karyawan: int


class DashboardPendingCountResponse(BaseModel):
  pending: int


class DashboardGaHadirCountResponse(BaseModel):
  ga_hadir: int


class DashboardKaryawanItemResponse(BaseModel):
  id_karyawan: str
  nama_karyawan: str
  email_karyawan: str | None = None
  nomor_hp: str | None = None
  foto_profile: str | None = None
  tanggal_rekrut: date | None = None
  status: str
  posisi: str | None = None
  departemen_id: int
  nama_departemen: str


class DashboardPendingItemResponse(BaseModel):
  id: int
  id_karyawan: str
  id_absensi: int
  tanggal_absen: datetime
  check_in: datetime | None = None
  check_out: datetime | None = None
  pengajuan: str
  status_absen: str
  nama_karyawan: str | None = None
  email_karyawan: str | None = None
  nomor_hp: str | None = None
  foto_profile: str | None = None
  tanggal_rekrut: date | None = None
  status: str | None = None
  posisi: str | None = None
  id_departemen: int | None = None


class DashboardGaHadirItemResponse(BaseModel):
  id: int
  id_karyawan: str
  nama: str | None = None
  tanggal_absen: datetime
  pengajuan: str
  status_absen: str


class DataDashboardResponse(BaseModel):
  total_karyawan: DashboardKaryawanCountResponse
  total_karyawan_list: list[DashboardKaryawanItemResponse]
  absen_pending: DashboardPendingCountResponse
  absen_pending_list: list[DashboardPendingItemResponse]
  data_ga_hadir: DashboardGaHadirCountResponse
  ga_hadir_list: list[DashboardGaHadirItemResponse]


class PengajuanItemResponse(BaseModel):
  id_pengajuan: int
  id_karyawan: str
  tipe_pengajuan: str
  tanggal_mulai: date
  tanggal_akhir: date
  foto_lampiran: str | None = None
  keterangan: str | None = None
  status: str
  alasan_penolakan: str | None = None
  nama_karyawan: str | None = None
