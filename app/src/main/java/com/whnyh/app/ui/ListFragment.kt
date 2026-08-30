package com.whnyh.app.ui

import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.ArrayAdapter
import android.widget.AdapterView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.whnyh.kdk.R
import com.whnyh.app.data.Faculty
import com.whnyh.app.data.RetrofitClient
import kotlinx.coroutines.launch
import android.content.Intent

class ListFragment : Fragment(R.layout.fragment_list) {

    private lateinit var spinner: Spinner
    private lateinit var resultCount: TextView
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: BoardingHouseAdapter

    private var faculties: List<Faculty> = emptyList()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        spinner = view.findViewById(R.id.faculty_spinner)
        resultCount = view.findViewById(R.id.result_count)
        recyclerView = view.findViewById(R.id.boarding_house_list)

        adapter = BoardingHouseAdapter { bh ->
            val intent = Intent(requireContext(), BoardingHouseDetailActivity::class.java)
            intent.putExtra(BoardingHouseDetailActivity.EXTRA_BOARDING_HOUSE_ID, bh.id)
            startActivity(intent)
        }
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = adapter

        loadFaculties()
    }

    private fun loadFaculties() {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                faculties = RetrofitClient.api.getFaculties()

                // First entry is "All areas" (no faculty filter, no ranking) -
                // represented as null so we can tell it apart from a real ID.
                val labels = listOf("All areas (no ranking)") + faculties.map { it.name }
                val spinnerAdapter = ArrayAdapter(
                    requireContext(),
                    android.R.layout.simple_spinner_item,
                    labels
                )
                spinnerAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
                spinner.adapter = spinnerAdapter

                spinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(parent: AdapterView<*>?, v: View?, position: Int, id: Long) {
                        if (position == 0) {
                            loadBoardingHouses(facultyId = null)
                        } else {
                            loadBoardingHouses(facultyId = faculties[position - 1].id)
                        }
                    }
                    override fun onNothingSelected(parent: AdapterView<*>?) {}
                }

                // Triggers the initial "All areas" load via the listener above.
            } catch (e: Exception) {
                Log.e("KostFinder", "Failed to load faculties", e)
                Toast.makeText(requireContext(), "Couldn't load faculties", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadBoardingHouses(facultyId: Int?) {
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val results = if (facultyId != null) {
                    resultCount.text = "Ranked by suitability"
                    RetrofitClient.api.getRecommended(facultyId, limit = 20)
                } else {
                    resultCount.text = ""
                    RetrofitClient.api.getBoardingHouses()
                }
                adapter.submitList(results)
                resultCount.text = "${results.size} boarding house${if (results.size == 1) "" else "s"}" +
                        if (facultyId != null) " \u00b7 ranked by suitability" else ""
            } catch (e: Exception) {
                Log.e("KostFinder", "Failed to load boarding houses", e)
                Toast.makeText(requireContext(), "Couldn't load boarding houses", Toast.LENGTH_SHORT).show()
            }
        }
    }
}